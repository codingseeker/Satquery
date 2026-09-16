import torch
from transformers import (
    AutoProcessor,
    Qwen2_5_VLForConditionalGeneration,
    BitsAndBytesConfig,
)

MODEL_ID = "training/models/qwen25vl"


def main():
    print("CUDA:", torch.cuda.is_available())
    print("GPU:", torch.cuda.get_device_name(0))

    print("\nLoading processor...")
    processor = AutoProcessor.from_pretrained(MODEL_ID)

    print("Loading 4-bit model...")

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )

    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_ID,
        quantization_config=quantization_config,
        device_map="auto",
        torch_dtype=torch.float16,
        attn_implementation="eager",
    )

    print("\n========== SUCCESS ==========")
    print("Model loaded:", MODEL_ID)

    allocated = torch.cuda.memory_allocated() / (1024 ** 3)
    reserved = torch.cuda.memory_reserved() / (1024 ** 3)

    print(f"GPU allocated: {allocated:.2f} GB")
    print(f"GPU reserved:  {reserved:.2f} GB")


if __name__ == "__main__":
    main()