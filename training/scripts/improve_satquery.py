"""
improve_satquery.py

Improved QLoRA training for SatQuery AI.

REAL DATA:
    180 BigEarthNet training examples
    20 BigEarthNet development examples

Improvements:
    - Assistant-only loss
    - Gradient accumulation
    - Lower learning rate
    - Multiple epochs
    - Development loss after every epoch
    - Best adapter checkpoint
    - Local Qwen2.5-VL model
    - 4-bit NF4 quantization
    - LoRA

Hardware:
    NVIDIA RTX 3050 6 GB Laptop GPU
"""

import json
import os
import shutil
from pathlib import Path

import torch
from PIL import Image
from torch.optim import AdamW

from transformers import (
    get_cosine_schedule_with_warmup,
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
# CONFIG
# ============================================================

MODEL_PATH = "training/models/qwen25vl"

TRAIN_FILE = "training/data/processed/train.jsonl"
DEV_FILE = "training/data/processed/dev.jsonl"

OUTPUT_DIR = "training/models/satquery-improved-lora"
BEST_DIR = "training/models/satquery-best-lora"

EPOCHS = 15

LEARNING_RATE = 1e-4
WARMUP_RATIO = 0.1

MAX_LENGTH = 2048

GRADIENT_ACCUMULATION_STEPS = 4

PRINT_EVERY = 10

LORA_RANK = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
LORA_TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]


# ============================================================
# LOAD JSONL
# ============================================================

def load_jsonl(path):
    records = []

    with open(
        path,
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
# PREPARE MESSAGES
# ============================================================

def prepare_messages(record):

    messages = record["messages"]

    if len(messages) < 2:
        raise ValueError(
            f"Invalid messages for record {record['id']}"
        )

    user_message = messages[0]
    assistant_message = messages[1]

    image_path = None
    question_text = None

    # --------------------------------------------------------
    # Extract image path and question
    # --------------------------------------------------------

    for item in user_message["content"]:

        if item["type"] == "image":

            image_path = item["image"]

        elif item["type"] == "text":

            question_text = item["text"]

    if image_path is None:
        raise ValueError(
            f"No image found for record {record['id']}"
        )

    if question_text is None:
        raise ValueError(
            f"No question found for record {record['id']}"
        )

    image_path = Path(image_path)

    if not image_path.exists():

        raise FileNotFoundError(
            f"Image not found:\n{image_path}"
        )

    image = Image.open(
        image_path
    ).convert("RGB")

    # --------------------------------------------------------
    # Full conversation
    # --------------------------------------------------------

    
    system_msg = {
        "role": "system",
        "content": "You are a precise remote-sensing AI. Answer exactly and concisely in the required structured format (e.g. strict 'yes' or 'no', single letter for MCQ, exact coordinates for bounding boxes). Do not add conversational filler."
    }
    full_messages = [
        system_msg,
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": image,
                },
                {
                    "type": "text",
                    "text": question_text,
                },
            ],
        },
        {
            "role": "assistant",
            "content": assistant_message["content"],
        },
    ]

    # --------------------------------------------------------
    # Prompt-only conversation
    # --------------------------------------------------------

    
    system_msg = {
        "role": "system",
        "content": "You are a precise remote-sensing AI. Answer exactly and concisely in the required structured format (e.g. strict 'yes' or 'no', single letter for MCQ, exact coordinates for bounding boxes). Do not add conversational filler."
    }
    prompt_messages = [
        system_msg,
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": image,
                },
                {
                    "type": "text",
                    "text": question_text,
                },
            ],
        }
    ]

    return (
        full_messages,
        prompt_messages,
    )


# ============================================================
# BUILD TRAINING EXAMPLE
# ============================================================

def build_training_example(
    record,
    processor,
):

    (
        full_messages,
        prompt_messages,
    ) = prepare_messages(record)

    # --------------------------------------------------------
    # Full conversation text
    # --------------------------------------------------------

    full_text = processor.apply_chat_template(
        full_messages,
        tokenize=False,
        add_generation_prompt=False,
    )

    # --------------------------------------------------------
    # Prompt-only text
    #
    # generation prompt marks the position where the
    # assistant response begins.
    # --------------------------------------------------------

    prompt_text = processor.apply_chat_template(
        prompt_messages,
        tokenize=False,
        add_generation_prompt=True,
    )



    # --------------------------------------------------------
    # Visual inputs
    #
    # Your installed qwen_vl_utils version returns:
    #
    #     image_inputs
    #     video_inputs
    #
    # --------------------------------------------------------

    image_inputs, video_inputs, video_kwargs = process_vision_info(
        full_messages, return_video_kwargs=True
    )

    # Only pass video_kwargs when there are real videos. When there are no
    # videos, process_vision_info returns fps=[] which fails the processor's
    # type validator (expects int, float, or None — not an empty list).
    safe_video_kwargs = {}
    if video_inputs and video_kwargs:
        safe_video_kwargs = {
            k: v for k, v in video_kwargs.items()
            if v is not None and v != []
        }

    full_inputs = processor(
        text=[full_text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        truncation=True,
        max_length=MAX_LENGTH,
        return_tensors="pt",
        **safe_video_kwargs,
    )

    # --------------------------------------------------------
    # Prompt-only processor
    #
    # We use this only to determine the number of prompt
    # tokens that should be excluded from training loss.
    # --------------------------------------------------------

    prompt_inputs = processor(
        text=[prompt_text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        truncation=True,
        max_length=MAX_LENGTH,
        return_tensors="pt",
        **safe_video_kwargs,
    )

    prompt_length = (
        prompt_inputs["input_ids"].shape[1]
    )

    return (
        full_inputs,
        prompt_length,
    )


# ============================================================
# MOVE INPUTS TO DEVICE
# ============================================================

def move_inputs_to_device(
    inputs,
    device,
):

    output = {}

    for key, value in inputs.items():

        if torch.is_tensor(value):

            output[key] = value.to(
                device
            )

        else:

            output[key] = value

    return output


# ============================================================
# CREATE ASSISTANT-ONLY LABELS
# ============================================================

def create_labels(
    inputs,
    prompt_length,
    processor,
):

    labels = inputs[
        "input_ids"
    ].clone()

    # --------------------------------------------------------
    # Ignore prompt tokens
    # --------------------------------------------------------

    labels[:, :prompt_length] = -100

    # --------------------------------------------------------
    # Ignore padding
    # --------------------------------------------------------

    pad_token_id = (
        processor.tokenizer.pad_token_id
    )

    if pad_token_id is not None:

        labels[
            labels == pad_token_id
        ] = -100

    return labels


# ============================================================
# TRAIN ONE EPOCH
# ============================================================

def train_one_epoch(
    model,
    processor,
    optimizer,
    train_data,
    device,
    epoch_number,
):

    model.train()

    optimizer.zero_grad(
        set_to_none=True
    )

    running_loss = 0.0

    accumulated_steps = 0

    total_steps = len(train_data)

    for index, record in enumerate(
        train_data,
        start=1,
    ):

        # ----------------------------------------------------
        # Prepare example
        # ----------------------------------------------------

        (
            inputs,
            prompt_length,
        ) = build_training_example(
            record,
            processor,
        )

        # ----------------------------------------------------
        # Move tensors to GPU
        # ----------------------------------------------------

        inputs = move_inputs_to_device(
            inputs,
            device,
        )

        # ----------------------------------------------------
        # Assistant-only labels
        # ----------------------------------------------------

        labels = create_labels(
            inputs,
            prompt_length,
            processor,
        )

        inputs["labels"] = labels

        # ----------------------------------------------------
        # Forward pass
        # ----------------------------------------------------

        outputs = model(
            **inputs
        )

        loss = outputs.loss

        loss_value = loss.item()

        running_loss += loss_value

        # ----------------------------------------------------
        # Gradient accumulation
        # ----------------------------------------------------

        scaled_loss = (
            loss
            / GRADIENT_ACCUMULATION_STEPS
        )

        scaled_loss.backward()

        accumulated_steps += 1

        # ----------------------------------------------------
        # Optimizer step
        # ----------------------------------------------------

        if (
            accumulated_steps
            >= GRADIENT_ACCUMULATION_STEPS
            or index == total_steps
        ):

            optimizer.step()

            optimizer.zero_grad(
                set_to_none=True
            )

            accumulated_steps = 0

        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        if (
            index == 1
            or index % PRINT_EVERY == 0
            or index == total_steps
        ):

            average_loss = (
                running_loss
                / index
            )

            gpu_allocated = (
                torch.cuda.memory_allocated()
                / (1024 ** 3)
            )

            gpu_reserved = (
                torch.cuda.memory_reserved()
                / (1024 ** 3)
            )

            print(
                f"Epoch {epoch_number} | "
                f"Step {index}/{total_steps} | "
                f"Loss {loss_value:.4f} | "
                f"Avg {average_loss:.4f} | "
                f"GPU "
                f"{gpu_allocated:.2f}/"
                f"{gpu_reserved:.2f} GB"
            )

        # ----------------------------------------------------
        # Free references
        # ----------------------------------------------------

        del inputs
        del outputs
        del loss
        del scaled_loss

    return (
        running_loss
        / total_steps
    )


# ============================================================
# DEVELOPMENT LOSS
# ============================================================

@torch.no_grad()
def evaluate_loss(
    model,
    processor,
    dev_data,
    device,
):

    model.eval()

    running_loss = 0.0

    for record in dev_data:

        (
            inputs,
            prompt_length,
        ) = build_training_example(
            record,
            processor,
        )

        inputs = move_inputs_to_device(
            inputs,
            device,
        )

        labels = create_labels(
            inputs,
            prompt_length,
            processor,
        )

        inputs["labels"] = labels

        outputs = model(
            **inputs
        )

        running_loss += (
            outputs.loss.item()
        )

        del inputs
        del outputs
        del labels

    return (
        running_loss
        / len(dev_data)
    )


# ============================================================
# SAVE BEST MODEL
# ============================================================

def save_best_model(
    model,
    processor,
):

    if os.path.exists(
        BEST_DIR
    ):

        shutil.rmtree(
            BEST_DIR
        )

    os.makedirs(
        BEST_DIR,
        exist_ok=True,
    )

    model.save_pretrained(
        BEST_DIR
    )

    processor.save_pretrained(
        BEST_DIR
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "SATQUERY AI — IMPROVED QLoRA TRAINING"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # CUDA
    # --------------------------------------------------------

    if not torch.cuda.is_available():

        raise RuntimeError(
            "CUDA is not available."
        )

    print(
        "GPU:",
        torch.cuda.get_device_name(0)
    )

    total_vram = (
        torch.cuda.get_device_properties(0)
        .total_memory
        / (1024 ** 3)
    )

    print(
        f"Total VRAM: "
        f"{total_vram:.2f} GB"
    )

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    print(
        "\nLoading REAL BigEarthNet data..."
    )

    train_data = load_jsonl(
        TRAIN_FILE
    )

    dev_data = load_jsonl(
        DEV_FILE
    )

    print(
        f"Training examples: "
        f"{len(train_data)}"
    )

    print(
        f"Development examples: "
        f"{len(dev_data)}"
    )

    if len(train_data) == 0:

        raise RuntimeError(
            "Training dataset is empty."
        )

    if len(dev_data) == 0:

        raise RuntimeError(
            "Development dataset is empty."
        )

    # --------------------------------------------------------
    # Processor
    # --------------------------------------------------------

    print(
        "\nLoading processor..."
    )

    processor = AutoProcessor.from_pretrained(
        MODEL_PATH,
        local_files_only=True,
    )

    # --------------------------------------------------------
    # 4-bit configuration
    # --------------------------------------------------------

    quantization_config = (
        BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
    )

    # --------------------------------------------------------
    # Load Qwen2.5-VL
    # --------------------------------------------------------

    print(
        "\nLoading Qwen2.5-VL in 4-bit..."
    )

    model = (
        Qwen2_5_VLForConditionalGeneration
        .from_pretrained(
            MODEL_PATH,
            quantization_config=quantization_config,
            device_map="auto",
            torch_dtype=torch.float16,
            attn_implementation="sdpa",
            local_files_only=True,
        )
    )

    model.config.use_cache = False

    # --------------------------------------------------------
    # Prepare QLoRA
    # --------------------------------------------------------

    print(
        "\nPreparing model for k-bit training..."
    )

    model = prepare_model_for_kbit_training(
        model
    )

    # --------------------------------------------------------
    # LoRA
    # --------------------------------------------------------

    print(
        "Attaching LoRA..."
    )

    lora_config = LoraConfig(
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=LORA_TARGET_MODULES,
    )

    model = get_peft_model(
        model,
        lora_config,
    )

    model.print_trainable_parameters()

    # --------------------------------------------------------
    # Device
    # --------------------------------------------------------

    device = next(
        model.parameters()
    ).device

    print(
        "Model device:",
        device
    )

    # --------------------------------------------------------
    # Optimizer
    # --------------------------------------------------------

    trainable_parameters = [
        parameter
        for parameter in model.parameters()
        if parameter.requires_grad
    ]

    optimizer = AdamW(
        trainable_parameters,
        lr=LEARNING_RATE,
    )

    # --------------------------------------------------------
    # Tracking
    # --------------------------------------------------------

    best_dev_loss = float("inf")

    best_epoch = 0

    train_losses = []

    dev_losses = []

    # --------------------------------------------------------
    # Configuration summary
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "IMPROVED TRAINING CONFIGURATION"
    )

    print(
        "=" * 70
    )

    print(
        f"Epochs: "
        f"{EPOCHS}"
    )

    print(
        f"Learning rate: "
        f"{LEARNING_RATE}"
    )

    print(
        f"Gradient accumulation: "
        f"{GRADIENT_ACCUMULATION_STEPS}"
    )

    print(
        f"LoRA rank: {LORA_RANK}"
    )

    print(
        f"LoRA alpha: {LORA_ALPHA}"
    )

    print(
        "LoRA dropout: 0.05"
    )

    print(
        "Quantization: 4-bit NF4"
    )

    print(
        f"Max sequence length: "
        f"{MAX_LENGTH}"
    )

    print(
        f"Train samples: "
        f"{len(train_data)}"
    )

    print(
        f"Dev samples: "
        f"{len(dev_data)}"
    )

    print(
        "Loss: ASSISTANT ONLY"
    )

    print(
        "=" * 70
    )

    # --------------------------------------------------------
    # Epoch loop
    # --------------------------------------------------------

    for epoch in range(
        EPOCHS
    ):

        print(
            "\n" + "=" * 70
        )

        print(
            f"EPOCH {epoch + 1}/{EPOCHS}"
        )

        print(
            "=" * 70
        )

        # ----------------------------------------------------
        # Training
        # ----------------------------------------------------

        train_loss = train_one_epoch(
            model=model,
            processor=processor,
            optimizer=optimizer,
            train_data=train_data,
            device=device,
            epoch_number=epoch + 1,
        )

        train_losses.append(
            train_loss
        )

        print(
            f"\nTraining loss: "
            f"{train_loss:.4f}"
        )

        # ----------------------------------------------------
        # Development evaluation
        # ----------------------------------------------------

        print(
            "\nEvaluating development loss..."
        )

        dev_loss = evaluate_loss(
            model=model,
            processor=processor,
            dev_data=dev_data,
            device=device,
        )

        dev_losses.append(
            dev_loss
        )

        print(
            f"Development loss: "
            f"{dev_loss:.4f}"
        )

        # ----------------------------------------------------
        # Best checkpoint
        # ----------------------------------------------------

        if dev_loss < best_dev_loss:

            best_dev_loss = dev_loss

            best_epoch = (
                epoch + 1
            )

            print(
                "\nNEW BEST MODEL"
            )

            print(
                f"Best dev loss: "
                f"{best_dev_loss:.4f}"
            )

            save_best_model(
                model,
                processor,
            )

            print(
                "Best adapter saved to:"
            )

            print(
                Path(
                    BEST_DIR
                ).resolve()
            )

    # --------------------------------------------------------
    # Create final output directory
    # --------------------------------------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Save final adapter
    # --------------------------------------------------------

    print(
        "\nSaving final adapter..."
    )

    model.save_pretrained(
        OUTPUT_DIR
    )

    processor.save_pretrained(
        OUTPUT_DIR
    )

    # --------------------------------------------------------
    # Training metadata
    # --------------------------------------------------------

    metadata = {
        "base_model": MODEL_PATH,
        "train_file": TRAIN_FILE,
        "dev_file": DEV_FILE,
        "train_samples": len(train_data),
        "dev_samples": len(dev_data),
        "epochs": EPOCHS,
        "learning_rate": LEARNING_RATE,
        "gradient_accumulation_steps":
            GRADIENT_ACCUMULATION_STEPS,
        "lora_rank": 8,
        "lora_alpha": 16,
        "lora_dropout": 0.05,
        "quantization": "4-bit NF4",
        "loss_type": "assistant_only",
        "max_length": MAX_LENGTH,
        "train_losses": train_losses,
        "dev_losses": dev_losses,
        "best_epoch": best_epoch,
        "best_dev_loss": best_dev_loss,
    }

    metadata_path = (
        Path(OUTPUT_DIR)
        / "training_metadata.json"
    )

    with open(
        metadata_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            metadata,
            f,
            indent=2,
        )

    # --------------------------------------------------------
    # GPU statistics
    # --------------------------------------------------------

    peak_memory = (
        torch.cuda.max_memory_allocated()
        / (1024 ** 3)
    )

    # --------------------------------------------------------
    # Final report
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "IMPROVED TRAINING COMPLETE"
    )

    print(
        "=" * 70
    )

    print(
        f"Best epoch: "
        f"{best_epoch}"
    )

    print(
        f"Best development loss: "
        f"{best_dev_loss:.4f}"
    )

    print(
        f"Peak GPU memory: "
        f"{peak_memory:.2f} GB"
    )

    print(
        "\nFinal adapter:"
    )

    print(
        Path(
            OUTPUT_DIR
        ).resolve()
    )

    print(
        "\nBest adapter:"
    )

    print(
        Path(
            BEST_DIR
        ).resolve()
    )

    print(
        "\nTraining losses:"
    )

    for i, value in enumerate(
        train_losses,
        start=1,
    ):

        print(
            f"  Epoch {i}: "
            f"{value:.4f}"
        )

    print(
        "\nDevelopment losses:"
    )

    for i, value in enumerate(
        dev_losses,
        start=1,
    ):

        print(
            f"  Epoch {i}: "
            f"{value:.4f}"
        )

    print(
        "\nMetadata:"
    )

    print(
        metadata_path.resolve()
    )

    print(
        "\nSATQUERY IMPROVED TRAINING FINISHED."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()