"""
evaluate_satquery.py
--------------------
Loads:
    Qwen2.5-VL-3B-Instruct
    +
    SatQuery QLoRA adapter
and evaluates the trained model on the held-out
REAL BigEarthNet development set.
It also supports testing a single custom image/question.
"""

import argparse
import json
import os
from pathlib import Path

import torch
from PIL import Image

from transformers import (
    AutoProcessor,
    Qwen2_5_VLForConditionalGeneration,
    BitsAndBytesConfig,
)

from peft import PeftModel

from qwen_vl_utils import process_vision_info


# ============================================================
# PATHS
# ============================================================

BASE_MODEL = "training/models/qwen25vl"

ADAPTER_PATH = "training/models/satquery-best-lora"

DEV_FILE = "training/data/processed/dev.jsonl"

RESULTS_FILE = "training/outputs/satquery_evaluation.json"


# ============================================================
# SETTINGS
# ============================================================

MAX_NEW_TOKENS = 128


# ============================================================
# LOAD MODEL
# ============================================================

def load_model():

    print("=" * 70)
    print("SATQUERY AI — LOADING TRAINED MODEL")
    print("=" * 70)

    # --------------------------------------------------------
    # CUDA check
    # --------------------------------------------------------

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is not available."
        )

    print(
        "GPU:",
        torch.cuda.get_device_name(0)
    )

    # --------------------------------------------------------
    # Processor
    # --------------------------------------------------------

    print("\nLoading processor...")

    processor = AutoProcessor.from_pretrained(
        BASE_MODEL,
        local_files_only=True,
    )

    # --------------------------------------------------------
    # Quantization
    # --------------------------------------------------------

    print("\nPreparing 4-bit quantization...")

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )

    # --------------------------------------------------------
    # Base model
    # --------------------------------------------------------

    print("\nLoading base Qwen2.5-VL...")

    model = (
        Qwen2_5_VLForConditionalGeneration
        .from_pretrained(
            BASE_MODEL,
            quantization_config=quantization_config,
            device_map="auto",
            torch_dtype=torch.float16,
            attn_implementation="eager",
            local_files_only=True,
        )
    )

    # --------------------------------------------------------
    # Check adapter
    # --------------------------------------------------------

    adapter_config = (
        Path(ADAPTER_PATH)
        / "adapter_config.json"
    )

    if not adapter_config.exists():
        raise FileNotFoundError(
            "Trained LoRA adapter was not found:\n"
            f"{Path(ADAPTER_PATH).resolve()}"
        )

    # --------------------------------------------------------
    # Load trained LoRA
    # --------------------------------------------------------

    print(
        "\nLoading trained SatQuery LoRA adapter..."
    )

    model = PeftModel.from_pretrained(
        model,
        ADAPTER_PATH,
        is_trainable=False,
        local_files_only=True,
    )

    model.eval()

    print(
        "\nModel + adapter loaded successfully."
    )

    return model, processor


# ============================================================
# BUILD QWEN MESSAGES
# ============================================================

def build_messages(
    image_path,
    question,
):
    """
    Construct a Qwen2.5-VL image + text conversation.
    """

    image = Image.open(
        image_path
    ).convert("RGB")

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": image,
                },
                {
                    "type": "text",
                    "text": question,
                },
            ],
        }
    ]

    return messages


# ============================================================
# GENERATE ANSWER
# ============================================================

@torch.inference_mode()
def generate_answer(
    model,
    processor,
    image_path,
    question,
):
    """
    Run one natural-language query against one satellite image.
    """

    image_path = Path(
        image_path
    )

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found:\n{image_path}"
        )

    # --------------------------------------------------------
    # Build conversation
    # --------------------------------------------------------

    messages = build_messages(
        image_path,
        question,
    )

    # --------------------------------------------------------
    # Qwen chat template
    # --------------------------------------------------------

    text = processor.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    # --------------------------------------------------------
    # Extract visual input
    #
    # IMPORTANT:
    # Your installed qwen_vl_utils version returns TWO values:
    #
    #     image_inputs
    #     video_inputs
    #
    # --------------------------------------------------------

    image_inputs, video_inputs = process_vision_info(
        messages
    )

    # --------------------------------------------------------
    # Processor
    # --------------------------------------------------------

    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )

    # --------------------------------------------------------
    # Move tensors to model device
    # --------------------------------------------------------

    model_device = next(
        model.parameters()
    ).device

    for key, value in inputs.items():

        if torch.is_tensor(value):

            inputs[key] = value.to(
                model_device
            )

    # --------------------------------------------------------
    # Generate
    # --------------------------------------------------------

    generated_ids = model.generate(
        **inputs,
        max_new_tokens=MAX_NEW_TOKENS,
        do_sample=False,
        use_cache=True,
    )

    # --------------------------------------------------------
    # Remove input/prompt tokens
    # --------------------------------------------------------

    input_length = (
        inputs["input_ids"].shape[1]
    )

    generated_ids = generated_ids[
        :,
        input_length:
    ]

    # --------------------------------------------------------
    # Decode
    # --------------------------------------------------------

    answer = processor.batch_decode(
        generated_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True,
    )[0]

    return answer.strip()


# ============================================================
# LOAD DEVELOPMENT DATA
# ============================================================

def load_dev_data():

    if not os.path.exists(
        DEV_FILE
    ):
        raise FileNotFoundError(
            f"Development file not found:\n{DEV_FILE}"
        )

    records = []

    with open(
        DEV_FILE,
        "r",
        encoding="utf-8",
    ) as f:

        for line in f:

            line = line.strip()

            if line:
                records.append(
                    json.loads(line)
                )

    return records


# ============================================================
# EXTRACT QUESTION
# ============================================================

def extract_question(record):

    messages = record["messages"]

    for item in messages[0]["content"]:

        if item["type"] == "text":

            return item["text"]

    raise ValueError(
        f"No question found for {record['id']}"
    )


# ============================================================
# EXTRACT EXPECTED ANSWER
# ============================================================

def extract_expected_answer(record):

    messages = record["messages"]

    for item in messages[1]["content"]:

        if item["type"] == "text":

            return item["text"]

    raise ValueError(
        f"No expected answer found for {record['id']}"
    )


# ============================================================
# NORMALIZE ANSWERS
# ============================================================

def normalize_text(text):

    return (
        text
        .strip()
        .lower()
        .replace("\n", " ")
        .replace("  ", " ")
    )


# ============================================================
# EVALUATE DEVELOPMENT SET
# ============================================================

def evaluate_dev_set(
    model,
    processor,
):

    records = load_dev_data()

    print("\n" + "=" * 70)
    print("DEVELOPMENT SET EVALUATION")
    print("=" * 70)

    print(
        f"Development examples: {len(records)}"
    )

    results = []

    exact_matches = 0

    # --------------------------------------------------------
    # Evaluate every development example
    # --------------------------------------------------------

    for index, record in enumerate(
        records,
        start=1,
    ):

        image_path = record["image"]

        question = extract_question(
            record
        )

        expected = extract_expected_answer(
            record
        )

        print(
            f"\n[{index}/{len(records)}]"
        )

        print(
            "ID:",
            record["id"]
        )

        print(
            "Task:",
            record["task"]
        )

        print(
            "Question:",
            question
        )

        print(
            "Expected:",
            expected
        )

        try:

            prediction = generate_answer(
                model=model,
                processor=processor,
                image_path=image_path,
                question=question,
            )

            error = None

        except Exception as exc:

            print(
                "ERROR:",
                repr(exc)
            )

            prediction = ""

            error = repr(exc)

        # ----------------------------------------------------
        # Print prediction
        # ----------------------------------------------------

        print(
            "Predicted:",
            prediction
        )

        # ----------------------------------------------------
        # Exact match
        # ----------------------------------------------------

        normalized_expected = normalize_text(
            expected
        )

        normalized_prediction = normalize_text(
            prediction
        )

        exact_match = (
            normalized_expected
            == normalized_prediction
        )

        if exact_match:
            exact_matches += 1

        print(
            "Exact match:",
            exact_match
        )

        # ----------------------------------------------------
        # Store result
        # ----------------------------------------------------

        results.append(
            {
                "id": record["id"],
                "task": record["task"],
                "category": record.get(
                    "category"
                ),
                "image": image_path,
                "question": question,
                "expected": expected,
                "prediction": prediction,
                "exact_match": exact_match,
                "error": error,
            }
        )

    # --------------------------------------------------------
    # Overall metrics
    # --------------------------------------------------------

    total = len(results)

    exact_match_rate = (
        exact_matches / total
        if total > 0
        else 0.0
    )

    # --------------------------------------------------------
    # Per-task metrics
    # --------------------------------------------------------

    task_statistics = {}

    for result in results:

        task = result["task"]

        if task not in task_statistics:

            task_statistics[task] = {
                "total": 0,
                "exact_matches": 0,
            }

        task_statistics[task]["total"] += 1

        if result["exact_match"]:

            task_statistics[task][
                "exact_matches"
            ] += 1

    for task, stats in task_statistics.items():

        task_total = stats["total"]

        task_matches = stats[
            "exact_matches"
        ]

        stats["exact_match_rate"] = (
            task_matches / task_total
            if task_total > 0
            else 0.0
        )

    # --------------------------------------------------------
    # Final print
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("DEVELOPMENT EVALUATION COMPLETE")
    print("=" * 70)

    print(
        f"Exact matches: "
        f"{exact_matches}/{total}"
    )

    print(
        f"Exact-match rate: "
        f"{exact_match_rate * 100:.2f}%"
    )

    print(
        "\nPer-task results:"
    )

    for task, stats in task_statistics.items():

        print(
            f"  {task}: "
            f"{stats['exact_matches']}/"
            f"{stats['total']} "
            f"("
            f"{stats['exact_match_rate'] * 100:.2f}%"
            f")"
        )

    # --------------------------------------------------------
    # Save evaluation results
    # --------------------------------------------------------

    results_directory = os.path.dirname(
        RESULTS_FILE
    )

    os.makedirs(
        results_directory,
        exist_ok=True,
    )

    output = {
        "base_model": BASE_MODEL,
        "adapter": ADAPTER_PATH,
        "development_file": DEV_FILE,
        "development_examples": total,
        "exact_matches": exact_matches,
        "exact_match_rate": exact_match_rate,
        "task_statistics": task_statistics,
        "results": results,
    }

    with open(
        RESULTS_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(
        "\nResults saved to:"
    )

    print(
        Path(
            RESULTS_FILE
        ).resolve()
    )

    return results


# ============================================================
# CUSTOM QUERY MODE
# ============================================================

def run_custom_query(
    model,
    processor,
    image_path,
    question,
):

    print("\n" + "=" * 70)
    print("SATQUERY CUSTOM QUERY")
    print("=" * 70)

    print(
        "Image:",
        image_path
    )

    print(
        "Question:",
        question
    )

    print(
        "\nGenerating answer..."
    )

    answer = generate_answer(
        model=model,
        processor=processor,
        image_path=image_path,
        question=question,
    )

    print(
        "\nAnswer:"
    )

    print(answer)

    return answer


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the trained SatQuery "
            "Qwen2.5-VL LoRA adapter."
        )
    )

    parser.add_argument(
        "--image",
        type=str,
        default=None,
        help=(
            "Path to a satellite RGB image."
        ),
    )

    parser.add_argument(
        "--question",
        type=str,
        default=None,
        help=(
            "Natural-language satellite query."
        ),
    )

    parser.add_argument(
        "--dev",
        action="store_true",
        help=(
            "Evaluate the 20-example "
            "development set."
        ),
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # Validate custom-query arguments
    # --------------------------------------------------------

    if (
        (args.image is None)
        != (args.question is None)
    ):

        raise ValueError(
            "For custom query mode, "
            "--image and --question "
            "must be provided together."
        )

    # --------------------------------------------------------
    # Load trained model
    # --------------------------------------------------------

    model, processor = load_model()

    # --------------------------------------------------------
    # Custom query mode
    # --------------------------------------------------------

    if (
        args.image is not None
        and args.question is not None
    ):

        run_custom_query(
            model=model,
            processor=processor,
            image_path=args.image,
            question=args.question,
        )

        return

    # --------------------------------------------------------
    # Development evaluation mode
    # --------------------------------------------------------

    if args.dev:

        evaluate_dev_set(
            model=model,
            processor=processor,
        )

        return

    # --------------------------------------------------------
    # No mode selected
    # --------------------------------------------------------

    print(
        "\nNo mode selected."
    )

    print(
        "\nDevelopment evaluation:"
    )

    print(
        "python training\\scripts\\evaluate_satquery.py --dev"
    )

    print(
        "\nCustom query:"
    )

    print(
        'python training\\scripts\\evaluate_satquery.py '
        '--image "training\\data\\images\\extracted\\s2\\IMAGE.png" '
        '--question "Is there arable land in this image?"'
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()