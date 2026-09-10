import json
import os
import random

MANIFEST = "training/data/processed/image_manifest.json"

TRAIN_OUTPUT = "training/data/processed/train.jsonl"
DEV_OUTPUT = "training/data/processed/dev.jsonl"

DEV_RATIO = 0.10
SEED = 42

def build_record(item):
    """
    Create one Qwen-style multimodal conversation.
    """

    image_path = item["s2_rgb"]

    # Convert Windows path separators to forward slashes.
    image_path = image_path.replace("\\", "/")

    question = item["question"].strip()
    answer = item["answer"].strip()

    task_type = item["type"]

    # Tell the model what task it is solving.
    # The original question/answer remain untouched.
    user_text = (
        f"Remote-sensing task: {task_type}\n\n"
        f"{question}"
    )

    return {
        "id": str(item["id"]),
        "image": image_path,
        "task": task_type,
        "category": item.get("category"),
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": image_path
                    },
                    {
                        "type": "text",
                        "text": user_text
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
        ]
    }

def main():

    print("Loading image manifest...")

    with open(
        MANIFEST,
        "r",
        encoding="utf-8"
    ) as f:
        manifest = json.load(f)

    print("Total matched examples:", len(manifest))

    records = []

    for item in manifest:

        image_path = item["s2_rgb"]

        if not os.path.exists(image_path):
            print("WARNING - missing image:", image_path)
            continue

        records.append(
            build_record(item)
        )

    print("Valid examples:", len(records))

    # Deterministic shuffle.
    random.seed(SEED)
    random.shuffle(records)

    dev_count = max(
        1,
        int(len(records) * DEV_RATIO)
    )

    dev_records = records[:dev_count]
    train_records = records[dev_count:]

    os.makedirs(
        os.path.dirname(TRAIN_OUTPUT),
        exist_ok=True
    )

    with open(
        TRAIN_OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:
        for record in train_records:
            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                ) + "\n"
            )

    with open(
        DEV_OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:
        for record in dev_records:
            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                ) + "\n"
            )

    print("\n========== DATASET CREATED ==========")
    print("Training examples:", len(train_records))
    print("Development examples:", len(dev_records))

    print("\nTraining task counts:")

    counts = {}

    for record in train_records:
        task = record["task"]
        counts[task] = counts.get(task, 0) + 1

    for task, count in counts.items():
        print(f"{task}: {count}")

    print("\nSaved:")
    print(TRAIN_OUTPUT)
    print(DEV_OUTPUT)

if __name__ == "__main__":
    main()
