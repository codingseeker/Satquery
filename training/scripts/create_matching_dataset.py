import os
import pandas as pd

TEXT_METADATA = "training/data/metadata/BigEarthNet.txt.parquet"
IMAGE_METADATA = "training/data/images/metadata_lithuania_summer.parquet"
OUTPUT = "training/data/processed/matching_first_run.parquet"

SAMPLES_PER_TYPE = 50


def main():
    print("Loading BigEarthNet.txt metadata...")
    text_df = pd.read_parquet(TEXT_METADATA)

    print("Loading available BigEarthNet v2.0 image metadata...")
    image_df = pd.read_parquet(IMAGE_METADATA)

    # Patch IDs that actually have pixels in our downloaded LMDB.
    available_s2 = set(image_df["patch_id"].astype(str))
    available_s1 = set(image_df["s1_name"].astype(str))

    print("Available S2 patches:", len(available_s2))
    print("Available S1 patches:", len(available_s1))

    # Only use official BigEarthNet.txt TRAIN annotations.
    candidates = text_df[
        (text_df["split"] == "train")
        & (text_df["patch_id"].astype(str).isin(available_s2))
        & (text_df["s1_name"].astype(str).isin(available_s1))
    ].copy()

    print("\nMatching training annotations:", len(candidates))

    print("\nTask availability:")
    print(candidates["type"].value_counts().to_string())

    selected = []

    for task_type in [
        "binary",
        "mcq",
        "captioning",
        "bounding box",
    ]:
        task_df = candidates[
            candidates["type"] == task_type
        ].copy()

        if len(task_df) < SAMPLES_PER_TYPE:
            raise RuntimeError(
                f"Only {len(task_df)} '{task_type}' examples "
                f"available, but {SAMPLES_PER_TYPE} are required."
            )

        selected.append(
            task_df.sample(
                n=SAMPLES_PER_TYPE,
                random_state=42
            )
        )

    result = (
        pd.concat(selected, ignore_index=True)
        .sample(frac=1, random_state=42)
        .reset_index(drop=True)
    )

    os.makedirs(
        os.path.dirname(OUTPUT),
        exist_ok=True
    )

    result.to_parquet(
        OUTPUT,
        index=False
    )

    print("\n========== MATCHED DATASET ==========")
    print("Annotations:", len(result))
    print("Unique S2 patches:", result["patch_id"].nunique())
    print("Unique S1 patches:", result["s1_name"].nunique())

    print("\nTask distribution:")
    print(result["type"].value_counts().to_string())

    print("\nCountry distribution:")
    print(result["country"].value_counts().to_string())

    print("\nSeason distribution:")
    print(result["season"].value_counts().to_string())

    print("\nSaved:")
    print(OUTPUT)


if __name__ == "__main__":
    main()
