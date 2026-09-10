# SatQuery

SatQuery is an experimental vision-language model for remote sensing. We fine-tuned `Qwen2.5-VL-3B-Instruct` to answer questions about satellite imagery, specifically focusing on identifying land cover, answering binary questions, and doing basic bounding box localization.

The model was trained entirely on a local RTX 3050 (6GB VRAM) laptop using 4-bit QLoRA.

## Dataset

We use a subset of the **BigEarthNet v2.0** dataset (specifically the Lithuania Summer split). 

The raw data consists of Sentinel-1 (SAR) and Sentinel-2 (Multispectral) patches stored in LMDB format. We extract the optical RGB bands and map them to text-based question-and-answer pairs across four tasks:
- `binary`: Yes/no questions about terrain features.
- `mcq`: Multiple-choice land cover classification.
- `captioning`: Detailed summarization of the landscape.
- `bounding box`: Localizing specific features.

## Project Layout

```
satquery-ai-service/
└── satai/
    ├── README.md
    └── training/
        ├── data/
        │   ├── images/       # LMDB files and extracted S1/S2 PNG/NPY patches
        │   ├── metadata/     # Raw BigEarthNet annotations
        │   └── processed/    # HuggingFace DatasetDict and JSONL files
        ├── models/
        │   ├── qwen25vl/           # Base model weights
        │   └── satquery-best-lora/ # The trained LoRA adapter
        ├── outputs/          # Logs and evaluation results
        └── scripts/          
            ├── extract_matching_pixels.py  # Unpacks LMDB to images
            ├── build_qwen_dataset.py       # Builds the conversational format
            ├── train.py                    # The QLoRA training loop
            ├── improve_satquery.py         # Modified training loop for better loss
            └── evaluate_satquery.py        # Runs inference on the dev set
```

## Results

On our held-out development set, the best checkpoint (`satquery-best-lora`, Epoch 5) achieved:
- **Dev Loss:** 0.4379
- **Exact Match:** 40.0%

*Note on the metric:* Exact match is a very strict string-matching metric. If the model outputs "The image shows a forest." and the ground truth is "This image shows a forest.", it counts as a failure. Qualitatively, the model has learned to identify land features quite well.

## Setup & Usage

### 1. Requirements
You'll need Python 3.11+ and a CUDA-capable GPU. Install the standard HuggingFace stack:
`pip install torch transformers peft bitsandbytes datasets qwen_vl_utils`

### 2. Running Evaluation
To test the trained adapter against the dev set:
```bash
python training/scripts/evaluate_satquery.py --dev
```

### 3. Inference (Loading the model)
If you want to plug the adapter into your own inference script, load the base model in 4-bit and apply the PEFT adapter:

```python
import torch
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration, BitsAndBytesConfig
from peft import PeftModel

# Load processor and base model
processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-3B-Instruct")
base_model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-VL-3B-Instruct", 
    quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16), 
    device_map="auto"
)

# Apply our trained LoRA
model = PeftModel.from_pretrained(base_model, "training/models/satquery-best-lora")

print("Ready for inference!")
```
