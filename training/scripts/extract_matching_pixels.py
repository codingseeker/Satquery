import json
import os
from typing import Any, Dict, List, Optional

import lmdb
import numpy as np
import pandas as pd
from PIL import Image
from safetensors import safe_open

ANNOTATIONS = "training/data/processed/matching_first_run.parquet"
LMDB_PATH = "training/data/images/BENv2_lithuania_summer.lmdb"

OUTPUT_ROOT = "training/data/images/extracted"

S2_DIR = os.path.join(OUTPUT_ROOT, "s2")
S1_DIR = os.path.join(OUTPUT_ROOT, "s1")

MANIFEST = "training/data/processed/image_manifest.json"

def percentile_normalize(array: np.ndarray) -> np.ndarray:
    """
    Convert a satellite band to uint8 for visualization.

    IMPORTANT:
    The original satellite values are preserved as .npy files.
    """
    array = np.asarray(array, dtype=np.float32)

    low = float(np.percentile(array, 2))
    high = float(np.percentile(array, 98))

    if (
        not np.isfinite(low)
        or not np.isfinite(high)
        or high <= low
    ):
        return np.zeros(
            array.shape,
            dtype=np.uint8
        )

    scaled = (array - low) / (high - low)
    scaled = np.clip(scaled, 0.0, 1.0)

    return (scaled * 255).astype(np.uint8)

def decode_safetensor_bytes(data: bytes) -> Dict[str, np.ndarray]:
    """
    Decode an in-memory SafeTensors byte buffer.

    LMDB contains SafeTensors bytes rather than normal
    .safetensors files, so we write the bytes to a temporary
    file and read them with the public safetensors API.
    """

    import tempfile

    with tempfile.NamedTemporaryFile(
        suffix=".safetensors",
        delete=True
    ) as temp:

        temp.write(data)
        temp.flush()

        result: Dict[str, np.ndarray] = {}

        with safe_open(
            temp.name,
            framework="numpy",
            device="cpu"
        ) as handle:

            for key in handle.keys():
                result[key] = handle.get_tensor(key)

        return result

def main() -> None:

    print("=" * 50)
    print("SATQUERY REAL PIXEL EXTRACTION")
    print("=" * 50)


    if not os.path.exists(ANNOTATIONS):
        raise FileNotFoundError(
            f"Annotation file not found:\n{ANNOTATIONS}"
        )

    if not os.path.exists(LMDB_PATH):
        raise FileNotFoundError(
            f"LMDB directory not found:\n{LMDB_PATH}"
        )

    # --------------------------------------------------------
    # Load matched annotations
    # --------------------------------------------------------

    print("\nLoading matched annotations...")

    df = pd.read_parquet(ANNOTATIONS)

    print(f"Annotations: {len(df)}")
    print(
        f"Unique S2 patches: "
        f"{df['patch_id'].nunique()}"
    )
    print(
        f"Unique S1 patches: "
        f"{df['s1_name'].nunique()}"
    )

    # --------------------------------------------------------
    # Prepare output directories
    # --------------------------------------------------------

    os.makedirs(S2_DIR, exist_ok=True)
    os.makedirs(S1_DIR, exist_ok=True)

    # --------------------------------------------------------
    # Open LMDB
    # --------------------------------------------------------

    print("\nOpening LMDB...")

    env = lmdb.open(
        LMDB_PATH,
        readonly=True,
        lock=False,
        readahead=True,
        max_readers=1,
    )

    manifest: List[Dict[str, Any]] = []

    missing_s2: List[str] = []
    missing_s1: List[str] = []

    try:

        with env.begin(write=False) as txn:

            for current_index, (_, row) in enumerate(
                df.iterrows(),
                start=1
            ):

                patch_id = str(row["patch_id"])
                s1_name = str(row["s1_name"])

                print(
                    f"\n[{current_index}/{len(df)}] "
                    f"{patch_id}"
                )

                # ====================================================
                # SENTINEL-2
                # ====================================================

                s2_key = patch_id.encode("utf-8")
                s2_bytes = txn.get(s2_key)

                if s2_bytes is None:
                    print(
                        "  ERROR: S2 record not found"
                    )
                    missing_s2.append(patch_id)
                    continue

                # Decode SafeTensors
                s2 = decode_safetensor_bytes(
                    bytes(s2_bytes)
                )

                # ----------------------------------------------------
                # Required RGB bands
                # ----------------------------------------------------

                required_s2_bands = [
                    "B02",
                    "B03",
                    "B04",
                ]

                missing_bands = [
                    band
                    for band in required_s2_bands
                    if band not in s2
                ]

                if missing_bands:
                    raise RuntimeError(
                        f"Missing S2 bands "
                        f"{missing_bands} "
                        f"for {patch_id}"
                    )

                # ----------------------------------------------------
                # Original pixel arrays
                # ----------------------------------------------------

                b02 = np.asarray(
                    s2["B02"]
                )

                b03 = np.asarray(
                    s2["B03"]
                )

                b04 = np.asarray(
                    s2["B04"]
                )

                # ----------------------------------------------------
                # Save original S2 bands
                # ----------------------------------------------------

                spectral_dir = os.path.join(
                    S2_DIR,
                    patch_id
                )

                os.makedirs(
                    spectral_dir,
                    exist_ok=True
                )

                np.save(
                    os.path.join(
                        spectral_dir,
                        "B02.npy"
                    ),
                    b02
                )

                np.save(
                    os.path.join(
                        spectral_dir,
                        "B03.npy"
                    ),
                    b03
                )

                np.save(
                    os.path.join(
                        spectral_dir,
                        "B04.npy"
                    ),
                    b04
                )

                # ----------------------------------------------------
                # RGB visualization
                #
                # Sentinel-2:
                # B04 = Red
                # B03 = Green
                # B02 = Blue
                # ----------------------------------------------------

                red = percentile_normalize(b04)
                green = percentile_normalize(b03)
                blue = percentile_normalize(b02)

                rgb = np.stack(
                    [
                        red,
                        green,
                        blue
                    ],
                    axis=-1
                )

                rgb_filename = (
                    f"{patch_id}.png"
                )

                rgb_path = os.path.join(
                    S2_DIR,
                    rgb_filename
                )

                Image.fromarray(
                    rgb,
                    mode="RGB"
                ).save(rgb_path)

                print(
                    f"  S2 RGB: {rgb_path}"
                )

                # ====================================================
                # SENTINEL-1
                # ====================================================

                s1_key = s1_name.encode("utf-8")
                s1_bytes = txn.get(s1_key)

                s1_dir: Optional[str] = None

                if s1_bytes is None:

                    print(
                        "  WARNING: S1 record not found"
                    )

                    missing_s1.append(
                        s1_name
                    )

                else:

                    s1 = decode_safetensor_bytes(
                        bytes(s1_bytes)
                    )

                    required_s1_bands = [
                        "VV",
                        "VH"
                    ]

                    missing_s1_bands = [
                        band
                        for band in required_s1_bands
                        if band not in s1
                    ]

                    if missing_s1_bands:
                        raise RuntimeError(
                            f"Missing S1 bands "
                            f"{missing_s1_bands} "
                            f"for {s1_name}"
                        )

                    # ------------------------------------------------
                    # Original SAR values
                    # ------------------------------------------------

                    vv = np.asarray(
                        s1["VV"],
                        dtype=np.float32
                    )

                    vh = np.asarray(
                        s1["VH"],
                        dtype=np.float32
                    )

                    # ------------------------------------------------
                    # Save SAR arrays
                    # ------------------------------------------------

                    s1_dir = os.path.join(
                        S1_DIR,
                        s1_name
                    )

                    os.makedirs(
                        s1_dir,
                        exist_ok=True
                    )

                    np.save(
                        os.path.join(
                            s1_dir,
                            "VV.npy"
                        ),
                        vv
                    )

                    np.save(
                        os.path.join(
                            s1_dir,
                            "VH.npy"
                        ),
                        vh
                    )

                    # ------------------------------------------------
                    # SAR visualizations
                    # ------------------------------------------------

                    vv_png = percentile_normalize(
                        vv
                    )

                    vh_png = percentile_normalize(
                        vh
                    )

                    Image.fromarray(
                        vv_png,
                        mode="L"
                    ).save(
                        os.path.join(
                            s1_dir,
                            "VV.png"
                        )
                    )

                    Image.fromarray(
                        vh_png,
                        mode="L"
                    ).save(
                        os.path.join(
                            s1_dir,
                            "VH.png"
                        )
                    )

                    print(
                        f"  S1 SAR: {s1_dir}"
                    )

                # ====================================================
                # MANIFEST
                # ====================================================

                category_value = row[
                    "category"
                ]

                category: Optional[str]

                if pd.isna(
                    category_value
                ):
                    category = None
                else:
                    category = str(
                        category_value
                    )

                manifest.append(
                    {
                        "id": int(row["ID"]),

                        "patch_id": patch_id,

                        "s1_name": s1_name,

                        "s2_rgb": rgb_path.replace(
                            "\\",
                            "/"
                        ),

                        "s2_b02": os.path.join(
                            spectral_dir,
                            "B02.npy"
                        ).replace(
                            "\\",
                            "/"
                        ),

                        "s2_b03": os.path.join(
                            spectral_dir,
                            "B03.npy"
                        ).replace(
                            "\\",
                            "/"
                        ),

                        "s2_b04": os.path.join(
                            spectral_dir,
                            "B04.npy"
                        ).replace(
                            "\\",
                            "/"
                        ),

                        "s1_directory": (
                            s1_dir.replace(
                                "\\",
                                "/"
                            )
                            if s1_dir is not None
                            else None
                        ),

                        "question": str(
                            row["input"]
                        ),

                        "answer": str(
                            row["output"]
                        ),

                        "type": str(
                            row["type"]
                        ),

                        "category": category,

                        "country": str(
                            row["country"]
                        ),

                        "season": str(
                            row["season"]
                        ),
                    }
                )

    finally:
        env.close()

    # ------------------------------------------------------------
    # Save manifest
    # ------------------------------------------------------------

    os.makedirs(
        os.path.dirname(MANIFEST),
        exist_ok=True
    )

    with open(
        MANIFEST,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            manifest,
            f,
            indent=2,
            ensure_ascii=False
        )

    # ------------------------------------------------------------
    # Final report
    # ------------------------------------------------------------

    print("\n" + "=" * 50)
    print("EXTRACTION COMPLETE")
    print("=" * 50)

    print(
        f"Requested annotations: "
        f"{len(df)}"
    )

    print(
        f"Successfully extracted: "
        f"{len(manifest)}"
    )

    print(
        f"Missing S2: "
        f"{len(missing_s2)}"
    )

    print(
        f"Missing S1: "
        f"{len(missing_s1)}"
    )

    print("\nS2 output:")
    print(
        os.path.abspath(S2_DIR)
    )

    print("\nS1 output:")
    print(
        os.path.abspath(S1_DIR)
    )

    print("\nManifest:")
    print(
        os.path.abspath(MANIFEST)
    )


if __name__ == "__main__":
    main()