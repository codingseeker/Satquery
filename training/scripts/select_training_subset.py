import os
import pandas as pd


METADATA_PATH = "training/data/metadata/BigEarthNet.txt.parquet"
OUTPUT_PATH = "training/data/processed/training_subset.parquet"

SAMPLES_PER_TYPE = 500


def main():
    print("Loading BigEarthNet.txt metadata...")
    df = pd.read_parquet(METADATA_PATH)

    # IMPORTANT:
    # Only use the official training split.
    train_df = df[df["split"] == "train"].copy()

    print(f"Total training rows available: {len(train_df):,}")

    selected_parts = []

    for task_type in ["binary", "mcq", "bounding box", "captioning"]:
        task_df = train_df[train_df["type"] == task_type].copy()

        print(f"{task_type}: {len(task_df):,} available")

        # Reproducible random selection.
        selected = task_df.sample(
            n=SAMPLES_PER_TYPE,
            random_state=42
        )

        selected_parts.append(selected)

    subset = pd.concat(selected_parts, ignore_index=True)

    # Shuffle final subset.
    subset = subset.sample(
        frac=1,
        random_state=42
    ).reset_index(drop=True)

    os.makedirs(
        os.path.dirname(OUTPUT_PATH),
        exist_ok=True
    )

    subset.to_parquet(OUTPUT_PATH, index=False)

    print("\n========== SELECTION COMPLETE ==========")
    print(f"Selected rows: {len(subset):,}")
    print("\nTask distribution:")
    print(subset["type"].value_counts())

    print("\nSplit distribution:")
    print(subset["split"].value_counts())

    print(f"\nSaved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()