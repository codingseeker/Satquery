import json
import os

from datasets import Dataset, DatasetDict, Image

TRAIN_JSONL = "training/data/processed/train.jsonl"
DEV_JSONL = "training/data/processed/dev.jsonl"

OUTPUT_DIR = "training/data/processed/qwen_dataset"

def read_jsonl(path):
    records = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    return records

def convert_record(record):
    image_path = record["image"]

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    question = None
    answer = None

    for message in record["messages"]:
        if message["role"] == "user":
            for item in message["content"]:
                if item["type"] == "text":
                    question = item["text"]

        elif message["role"] == "assistant":
            for item in message["content"]:
                if item["type"] == "text":
                    answer = item["text"]

    if not question or answer is None:
        raise ValueError(
            f"Invalid conversation for record {record['id']}"
        )

    return {
        "image": image_path,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image"
                    },
                    {
                        "type": "text",
                        "text": question
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": answer
                    }
                ]
            }
        ],
        "task": record["task"],
        "category": record.get("category")
    }

def build_split(path):
    records = read_jsonl(path)

    converted = [
        convert_record(record)
        for record in records
    ]

    dataset = Dataset.from_list(converted)

    # Tell Hugging Face that "image" is an actual image feature.
    dataset = dataset.cast_column(
        "image",
        Image()
    )

    return dataset

def main():
    print("Preparing training dataset...")

    train = build_split(TRAIN_JSONL)
    dev = build_split(DEV_JSONL)

    dataset = DatasetDict({
        "train": train,
        "validation": dev
    })

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    dataset.save_to_disk(OUTPUT_DIR)

    print("\n========== DATASET READY ==========")
    print("Train:", len(train))
    print("Validation:", len(dev))
    print("Saved:", OUTPUT_DIR)

if __name__ == "__main__":
    main()
