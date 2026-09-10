"""
train_smoke_test.py
-------------------
One-step QLoRA smoke test for Qwen2.5-VL-3B-Instruct
using one REAL BigEarthNet training example.

Hardware target:
    NVIDIA RTX 3050 6 GB Laptop GPU

Strategy:
    4-bit NF4 quantization + LoRA
"""

import json
import os

import torch
from PIL import Image

from transformers import (
    AutoProcessor,
    Qwen2_5_VLForConditionalGeneration,
    BitsAndBytesConfig,
)

from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
)

from qwen_vl_utils import process_vision_info


# ============================================================
# PATHS
# ============================================================

MODEL_PATH = "training/models/qwen25vl"

TRAIN_JSONL = "training/data/processed/train.jsonl"

OUTPUT_DIR = "training/models/satquery-smoke-test"


# ============================================================
# SETTINGS
# ============================================================

MAX_NEW_TOKENS = 128


# ============================================================
# LOAD FIRST REAL TRAINING EXAMPLE
# ============================================================

def load_first_example():
    with open(
        TRAIN_JSONL,
        "r",
        encoding="utf-8",
    ) as f:
        line = f.readline()

    if not line:
        raise RuntimeError(
            "train.jsonl is empty."
        )

    return json.loads(line)


# ============================================================
# BUILD MESSAGE FORMAT
# ============================================================

def build_text_messages(example):
    """
    Return the stored Qwen conversation.
    """

    return example["messages"]


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("SATQUERY QLoRA 1-STEP SMOKE TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # CUDA CHECK
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
    # LOAD REAL TRAINING EXAMPLE
    # --------------------------------------------------------

    example = load_first_example()

    image_path = example["image"]

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Training image not found:\n{image_path}"
        )

    print("\nReal training example:")
    print(
        "ID:",
        example["id"]
    )
    print(
        "Task:",
        example["task"]
    )
    print(
        "Image:",
        image_path
    )

    image = Image.open(
        image_path
    ).convert("RGB")

    print(
        "Image size:",
        image.size
    )

    # --------------------------------------------------------
    # LOAD PROCESSOR
    # --------------------------------------------------------

    print("\nLoading processor...")

    processor = AutoProcessor.from_pretrained(
        MODEL_PATH,
        local_files_only=True,
    )

    # --------------------------------------------------------
    # 4-BIT QUANTIZATION
    # --------------------------------------------------------

    print(
        "Loading 4-bit Qwen2.5-VL..."
    )

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )

    model = (
        Qwen2_5_VLForConditionalGeneration
        .from_pretrained(
            MODEL_PATH,
            quantization_config=quantization_config,
            device_map="auto",
            torch_dtype=torch.float16,
            attn_implementation="eager",
            local_files_only=True,
        )
    )

    # --------------------------------------------------------
    # PREPARE MODEL FOR QLoRA
    # --------------------------------------------------------

    print(
        "Preparing model for k-bit training..."
    )

    model = prepare_model_for_kbit_training(
        model
    )

    # --------------------------------------------------------
    # LoRA CONFIGURATION
    # --------------------------------------------------------

    print(
        "Attaching LoRA adapter..."
    )

    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        target_modules="all-linear",
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(
        model,
        lora_config,
    )

    model.print_trainable_parameters()

    # --------------------------------------------------------
    # BUILD QWEN MESSAGES
    # --------------------------------------------------------

    messages = build_text_messages(
        example
    )

    messages_for_model = []

    for message in messages:

        new_message = {
            "role": message["role"],
            "content": [],
        }

        for content in message["content"]:

            # Replace stored image path
            # with the actual PIL image.
            if content["type"] == "image":

                new_message["content"].append(
                    {
                        "type": "image",
                        "image": image,
                    }
                )

            else:

                new_message["content"].append(
                    content
                )

        messages_for_model.append(
            new_message
        )

    # --------------------------------------------------------
    # APPLY QWEN CHAT TEMPLATE
    # --------------------------------------------------------

    text = processor.apply_chat_template(
        messages_for_model,
        tokenize=False,
        add_generation_prompt=False,
    )

    # --------------------------------------------------------
    # PROCESS IMAGE / VIDEO INFORMATION
    # --------------------------------------------------------
    #
    # IMPORTANT:
    # Current qwen_vl_utils returns THREE values:
    #
    #   image_inputs
    #   video_inputs
    #   video_kwargs
    #
    # Our dataset uses images only, so video_kwargs is ignored.
    # --------------------------------------------------------

    image_inputs, video_inputs, _ = process_vision_info(
        messages_for_model
    )

    # --------------------------------------------------------
    # PROCESSOR → MODEL TENSORS
    # --------------------------------------------------------

    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )

    # --------------------------------------------------------
    # MOVE TENSORS TO GPU
    # --------------------------------------------------------

    processed_inputs = {}

    for key, value in inputs.items():

        if torch.is_tensor(value):

            processed_inputs[key] = value.to(
                model.device
            )

        else:

            processed_inputs[key] = value

    inputs = processed_inputs

    # --------------------------------------------------------
    # CREATE LABELS
    # --------------------------------------------------------

    labels = inputs[
        "input_ids"
    ].clone()

    pad_token_id = (
        processor.tokenizer.pad_token_id
    )

    if pad_token_id is not None:

        labels[
            labels == pad_token_id
        ] = -100

    # For this one-step smoke test,
    # the whole sequence is used as labels.
    #
    # The final training pipeline can use
    # assistant-only masking.

    inputs["labels"] = labels

    # --------------------------------------------------------
    # PRINT PROCESSOR OUTPUT
    # --------------------------------------------------------

    print("\nProcessor output:")

    for key, value in inputs.items():

        if hasattr(value, "shape"):

            print(
                f"{key}: {tuple(value.shape)}"
            )

    # --------------------------------------------------------
    # GPU MEMORY BEFORE FORWARD
    # --------------------------------------------------------

    torch.cuda.empty_cache()

    torch.cuda.reset_peak_memory_stats()

    before = (
        torch.cuda.memory_allocated()
        / (1024 ** 3)
    )

    print(
        f"\nGPU memory before forward: "
        f"{before:.2f} GB"
    )

    # --------------------------------------------------------
    # ONE TRAINING STEP
    # --------------------------------------------------------

    model.train()

    print(
        "\nRunning forward pass..."
    )

    outputs = model(
        **inputs
    )

    loss = outputs.loss

    print(
        f"Loss before backward: "
        f"{loss.item():.6f}"
    )

    # --------------------------------------------------------
    # BACKWARD
    # --------------------------------------------------------

    print(
        "\nRunning backward pass..."
    )

    loss.backward()

    print(
        "Backward pass successful."
    )

    # --------------------------------------------------------
    # OPTIMIZER
    # --------------------------------------------------------

    optimizer = torch.optim.AdamW(
        [
            parameter
            for parameter in model.parameters()
            if parameter.requires_grad
        ],
        lr=2e-4,
    )

    print(
        "\nRunning optimizer step..."
    )

    optimizer.step()

    optimizer.zero_grad(
        set_to_none=True
    )

    print(
        "Optimizer step successful."
    )

    # --------------------------------------------------------
    # SAVE LoRA ADAPTER
    # --------------------------------------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    model.save_pretrained(
        OUTPUT_DIR
    )

    processor.save_pretrained(
        OUTPUT_DIR
    )

    # --------------------------------------------------------
    # GPU MEMORY
    # --------------------------------------------------------

    after = (
        torch.cuda.memory_allocated()
        / (1024 ** 3)
    )

    peak = (
        torch.cuda.max_memory_allocated()
        / (1024 ** 3)
    )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60
    )

    print(
        "SMOKE TEST SUCCESSFUL"
    )

    print(
        "=" * 60
    )

    print(
        f"Loss: {loss.item():.6f}"
    )

    print(
        f"GPU memory after: "
        f"{after:.2f} GB"
    )

    print(
        f"Peak GPU memory: "
        f"{peak:.2f} GB"
    )

    print(
        "Adapter saved to:"
    )

    print(
        os.path.abspath(
            OUTPUT_DIR
        )
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()