import torch

from transformers import (
    Qwen2_5_VLForConditionalGeneration,
    BitsAndBytesConfig,
)

from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
)


MODEL_PATH = "training/models/qwen25vl"


def main():
    print("========================================")
    print("SATQUERY LoRA TEST")
    print("========================================")

    print("\nCUDA:", torch.cuda.is_available())

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU not available.")

    print("GPU:", torch.cuda.get_device_name(0))

    # ---------------------------------------------------------
    # 4-bit configuration
    # ---------------------------------------------------------

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )

    # ---------------------------------------------------------
    # Load local Qwen model
    # ---------------------------------------------------------

    print("\nLoading model...")

    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_PATH,
        quantization_config=quantization_config,
        device_map="auto",
        torch_dtype=torch.float16,
        attn_implementation="eager",
    )

    # ---------------------------------------------------------
    # Prepare model for QLoRA
    # ---------------------------------------------------------

    print("Preparing model for k-bit training...")

    model = prepare_model_for_kbit_training(
        model
    )

    # ---------------------------------------------------------
    # LoRA configuration
    # ---------------------------------------------------------

    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,

        # QLoRA-style target selection.
        target_modules="all-linear",

        bias="none",

        task_type="CAUSAL_LM",
    )

    # ---------------------------------------------------------
    # Attach LoRA
    # ---------------------------------------------------------

    print("Attaching LoRA adapter...")

    model = get_peft_model(
        model,
        lora_config
    )

    print("\n========================================")
    print("LoRA ATTACHED SUCCESSFULLY")
    print("========================================")

    model.print_trainable_parameters()

    allocated = (
        torch.cuda.memory_allocated()
        / (1024 ** 3)
    )

    reserved = (
        torch.cuda.memory_reserved()
        / (1024 ** 3)
    )

    print(
        f"\nGPU allocated: {allocated:.2f} GB"
    )

    print(
        f"GPU reserved:  {reserved:.2f} GB"
    )


if __name__ == "__main__":
    main()