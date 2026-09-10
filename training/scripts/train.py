"""
train.py
--------
Full QLoRA fine-tuning of Qwen2.5-VL-3B-Instruct
on the REAL SatQuery / BigEarthNet training dataset.

Hardware:
    NVIDIA RTX 3050 6 GB Laptop GPU

Training:
    4-bit NF4 quantization
    LoRA adapters
    180 real BigEarthNet training examples
    20 real BigEarthNet development examples
    3 epochs
"""

import json
import os
from pathlib import Path

import torch
from PIL import Image
from torch.optim import AdamW

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
# CONFIGURATION
# ============================================================

MODEL_PATH = "training/models/qwen25vl"

TRAIN_FILE = "training/data/processed/train.jsonl"
DEV_FILE = "training/data/processed/dev.jsonl"

OUTPUT_DIR = "training/models/satquery-qwen25vl-lora"

EPOCHS = 3
LEARNING_RATE = 2e-4
MAX_LENGTH = 2048

PRINT_EVERY = 10


# ============================================================
# DATASET LOADING
# ============================================================

def load_jsonl(path):
    """
    Load a JSONL file into a Python list.
    """

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
# BUILD ONE EXAMPLE
# ============================================================

def build_example(record, processor):
    """
    Convert one real dataset record into Qwen2.5-VL tensors.

    The stored JSON contains an image path.
    The image is opened and inserted into the Qwen message.
    """

    messages = record["messages"]

    if len(messages) < 2:
        raise ValueError(
            f"Invalid conversation for record {record['id']}"
        )

    user_message = messages[0]
    assistant_message = messages[1]

    # --------------------------------------------------------
    # Find image path
    # --------------------------------------------------------

    image_path = None

    for item in user_message["content"]:

        if item["type"] == "image":

            image_path = item["image"]
            break

    if image_path is None:
        raise ValueError(
            f"No image found for record {record['id']}"
        )

    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found:\n{image_path}"
        )

    # --------------------------------------------------------
    # Load real satellite image
    # --------------------------------------------------------

    image = Image.open(
        image_path
    ).convert("RGB")

    # --------------------------------------------------------
    # Extract question text
    # --------------------------------------------------------

    question_text = None

    for item in user_message["content"]:

        if item["type"] == "text":

            question_text = item["text"]
            break

    if question_text is None:
        raise ValueError(
            f"No text question found for record {record['id']}"
        )

    # --------------------------------------------------------
    # Construct Qwen messages
    # --------------------------------------------------------

    converted_messages = [
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
            "role": assistant_message["role"],
            "content": assistant_message["content"],
        },
    ]

    # --------------------------------------------------------
    # Apply Qwen chat template
    # --------------------------------------------------------

    text = processor.apply_chat_template(
        converted_messages,
        tokenize=False,
        add_generation_prompt=False,
    )

    # --------------------------------------------------------
    # Process multimodal inputs
    #
    # qwen_vl_utils currently returns:
    #
    #   image_inputs
    #   video_inputs
    #   video_kwargs
    #
    # We only use image inputs.
    # --------------------------------------------------------

    image_inputs, video_inputs, _ = process_vision_info(
        converted_messages
    )

    # --------------------------------------------------------
    # Convert to tensors
    # --------------------------------------------------------

    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        truncation=True,
        max_length=MAX_LENGTH,
        return_tensors="pt",
    )

    return inputs, text


# ============================================================
# MODEL LOADING
# ============================================================

def load_model_and_processor():

    print("\nLoading processor...")

    processor = AutoProcessor.from_pretrained(
        MODEL_PATH,
        local_files_only=True,
    )

    print("Loading 4-bit Qwen2.5-VL...")

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
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

    model.config.use_cache = False

    print(
        "Preparing model for k-bit training..."
    )

    model = prepare_model_for_kbit_training(
        model
    )

    return model, processor


# ============================================================
# LoRA
# ============================================================

def attach_lora(model):

    print("\nAttaching LoRA...")

    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules="all-linear",
    )

    model = get_peft_model(
        model,
        lora_config,
    )

    model.print_trainable_parameters()

    return model


# ============================================================
# MOVE INPUTS TO GPU
# ============================================================

def move_inputs_to_device(inputs, device):

    processed = {}

    for key, value in inputs.items():

        if torch.is_tensor(value):

            processed[key] = value.to(
                device
            )

        else:

            processed[key] = value

    return processed


# ============================================================
# CREATE LABELS
# ============================================================

def create_labels(inputs, processor):
    """
    Create language-model labels.

    Padding tokens are ignored.

    This version deliberately keeps the complete sequence
    for the first stable full training run.
    """

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
    """
    Train on all records for one epoch.
    """

    model.train()

    running_loss = 0.0

    total_steps = len(train_data)

    for index, record in enumerate(
        train_data,
        start=1,
    ):

        optimizer.zero_grad(
            set_to_none=True
        )

        # ----------------------------------------------------
        # Build one real example
        # ----------------------------------------------------

        inputs, _ = build_example(
            record,
            processor,
        )

        # ----------------------------------------------------
        # GPU
        # ----------------------------------------------------

        inputs = move_inputs_to_device(
            inputs,
            device,
        )

        # ----------------------------------------------------
        # Labels
        # ----------------------------------------------------

        labels = create_labels(
            inputs,
            processor,
        )

        inputs["labels"] = labels

        # ----------------------------------------------------
        # Forward
        # ----------------------------------------------------

        outputs = model(
            **inputs
        )

        loss = outputs.loss

        # ----------------------------------------------------
        # Backward
        # ----------------------------------------------------

        loss.backward()

        # ----------------------------------------------------
        # Optimizer update
        # ----------------------------------------------------

        optimizer.step()

        # ----------------------------------------------------
        # Record loss
        # ----------------------------------------------------

        loss_value = loss.item()

        running_loss += loss_value

        # ----------------------------------------------------
        # Progress output
        # ----------------------------------------------------

        if (
            index == 1
            or index % PRINT_EVERY == 0
            or index == total_steps
        ):

            average_loss = (
                running_loss / index
            )

            allocated = (
                torch.cuda.memory_allocated()
                / (1024 ** 3)
            )

            reserved = (
                torch.cuda.memory_reserved()
                / (1024 ** 3)
            )

            print(
                f"Epoch {epoch_number} | "
                f"Step {index}/{total_steps} | "
                f"Loss {loss_value:.4f} | "
                f"Avg {average_loss:.4f} | "
                f"GPU "
                f"{allocated:.2f}/"
                f"{reserved:.2f} GB"
            )

    return running_loss / total_steps


# ============================================================
# EVALUATION
# ============================================================

@torch.no_grad()
def evaluate(
    model,
    processor,
    dev_data,
    device,
):
    """
    Calculate average development loss.

    The 20 examples are never used for gradient updates.
    """

    model.eval()

    running_loss = 0.0

    for record in dev_data:

        inputs, _ = build_example(
            record,
            processor,
        )

        inputs = move_inputs_to_device(
            inputs,
            device,
        )

        labels = create_labels(
            inputs,
            processor,
        )

        inputs["labels"] = labels

        outputs = model(
            **inputs
        )

        running_loss += outputs.loss.item()

    return running_loss / len(dev_data)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "SATQUERY AI — FULL QLoRA TRAINING"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # GPU
    # --------------------------------------------------------

    if not torch.cuda.is_available():

        raise RuntimeError(
            "CUDA is not available."
        )

    gpu_name = (
        torch.cuda.get_device_name(0)
    )

    total_vram = (
        torch.cuda.get_device_properties(0)
        .total_memory
        / (1024 ** 3)
    )

    print(
        f"GPU: {gpu_name}"
    )

    print(
        f"Total VRAM: {total_vram:.2f} GB"
    )

    # --------------------------------------------------------
    # Dataset
    # --------------------------------------------------------

    print("\nLoading training data...")

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
    # Output directory
    # --------------------------------------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Model
    # --------------------------------------------------------

    model, processor = (
        load_model_and_processor()
    )

    # --------------------------------------------------------
    # LoRA
    # --------------------------------------------------------

    model = attach_lora(
        model
    )

    # --------------------------------------------------------
    # Device
    # --------------------------------------------------------

    device = next(
        model.parameters()
    ).device

    print(
        f"Model device: {device}"
    )

    # --------------------------------------------------------
    # Optimizer
    # --------------------------------------------------------

    optimizer = AdamW(
        [
            parameter
            for parameter in model.parameters()
            if parameter.requires_grad
        ],
        lr=LEARNING_RATE,
    )

    # --------------------------------------------------------
    # Training summary
    # --------------------------------------------------------

    print("\n" + "=" * 70)

    print(
        "TRAINING CONFIGURATION"
    )

    print(
        f"Epochs:           {EPOCHS}"
    )

    print(
        f"Learning rate:    {LEARNING_RATE}"
    )

    print(
        "LoRA rank:        8"
    )

    print(
        "LoRA alpha:       16"
    )

    print(
        "Quantization:     4-bit NF4"
    )

    print(
        f"Max sequence:     {MAX_LENGTH}"
    )

    print(
        f"Train examples:   {len(train_data)}"
    )

    print(
        f"Dev examples:     {len(dev_data)}"
    )

    print(
        f"Output directory: {OUTPUT_DIR}"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # Epoch loop
    # --------------------------------------------------------

    epoch_losses = []

    dev_losses = []

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
        # Train
        # ----------------------------------------------------

        train_loss = train_one_epoch(
            model=model,
            processor=processor,
            optimizer=optimizer,
            train_data=train_data,
            device=device,
            epoch_number=epoch + 1,
        )

        epoch_losses.append(
            train_loss
        )

        print(
            f"\nEpoch {epoch + 1} "
            f"training loss: "
            f"{train_loss:.4f}"
        )

        # ----------------------------------------------------
        # Development evaluation
        # ----------------------------------------------------

        print(
            "\nRunning development evaluation..."
        )

        dev_loss = evaluate(
            model=model,
            processor=processor,
            dev_data=dev_data,
            device=device,
        )

        dev_losses.append(
            dev_loss
        )

        print(
            f"Epoch {epoch + 1} "
            f"development loss: "
            f"{dev_loss:.4f}"
        )

        # ----------------------------------------------------
        # Save checkpoint
        # ----------------------------------------------------

        checkpoint_dir = os.path.join(
            OUTPUT_DIR,
            f"checkpoint-epoch-{epoch + 1}",
        )

        os.makedirs(
            checkpoint_dir,
            exist_ok=True,
        )

        model.save_pretrained(
            checkpoint_dir
        )

        processor.save_pretrained(
            checkpoint_dir
        )

        print(
            f"Checkpoint saved: "
            f"{checkpoint_dir}"
        )

    # --------------------------------------------------------
    # Final adapter
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "TRAINING COMPLETE"
    )

    print(
        "=" * 70
    )

    print(
        "\nSaving final LoRA adapter..."
    )

    model.save_pretrained(
        OUTPUT_DIR
    )

    processor.save_pretrained(
        OUTPUT_DIR
    )

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    metadata = {
        "base_model": MODEL_PATH,
        "dataset_train": TRAIN_FILE,
        "dataset_dev": DEV_FILE,
        "train_samples": len(train_data),
        "dev_samples": len(dev_data),
        "epochs": EPOCHS,
        "learning_rate": LEARNING_RATE,
        "lora_r": 8,
        "lora_alpha": 16,
        "lora_dropout": 0.05,
        "quantization": "4-bit NF4",
        "max_length": MAX_LENGTH,
        "train_losses": epoch_losses,
        "dev_losses": dev_losses,
    }

    metadata_path = os.path.join(
        OUTPUT_DIR,
        "training_metadata.json",
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

    print(
        f"\nPeak GPU memory: "
        f"{peak_memory:.2f} GB"
    )

    print(
        "\nTraining losses:"
    )

    for index, loss_value in enumerate(
        epoch_losses,
        start=1,
    ):

        print(
            f"  Epoch {index}: "
            f"{loss_value:.4f}"
        )

    print(
        "\nDevelopment losses:"
    )

    for index, loss_value in enumerate(
        dev_losses,
        start=1,
    ):

        print(
            f"  Epoch {index}: "
            f"{loss_value:.4f}"
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
        "\nTraining metadata:"
    )

    print(
        Path(
            metadata_path
        ).resolve()
    )

    print(
        "\nSATQUERY QLoRA TRAINING FINISHED."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()