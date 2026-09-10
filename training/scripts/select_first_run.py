import os
import pandas as pd

INPUT = "training/data/processed/training_subset.parquet"
OUTPUT = "training/data/processed/first_run.parquet"

SAMPLES_PER_TYPE = 50


def main():
    df = pd.read_parquet(INPUT)

    parts = []

    for task_type in ["binary", "mcq", "bounding box", "captioning"]:
        subset = df[df["type"] == task_type].sample(
            n=SAMPLES_PER_TYPE,
            random_state=42
        )
        parts.append(subset)

    result = (
        pd.concat(parts, ignore_index=True)
        .sample(frac=1, random_state=42)
        .reset_index(drop=True)
    )

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    result.to_parquet(OUTPUT, index=False)

    print("First training run created")
    print("Total annotations:", len(result))
    print("\nTask distribution:")
    print(result["type"].value_counts())
    print("\nUnique S2 patches:", result["patch_id"].nunique())
    print("Unique S1 patches:", result["s1_name"].nunique())
    print("\nSaved:", OUTPUT)


if __name__ == "__main__":
    main()