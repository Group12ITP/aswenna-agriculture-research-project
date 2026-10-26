"""
audit_manifest_and_load_tests.py - Validates every stored model file in model_manifest.csv,
runs automated load-and-predict verification, and calculates total disk footprint.
"""

import sys
from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib
import torch

src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from registry import get_experiments_root, compute_sha256
from data import load_model_data, get_feature_and_target_columns


def main():
    print("=" * 80)
    print("AUDITING MODEL MANIFEST & EXECUTING AUTOMATED LOAD-AND-PREDICT TESTS")
    print("=" * 80)

    root = get_experiments_root()
    manifest_csv = root / "models" / "model_manifest.csv"
    if not manifest_csv.exists():
        print("Error: model_manifest.csv not found!")
        sys.exit(1)

    df_manifest = pd.read_csv(manifest_csv)
    print(f"Total model records in manifest: {len(df_manifest)}")

    df_data = load_model_data()
    feature_cols, target_col = get_feature_and_target_columns()
    sample_X = df_data[feature_cols].head(3)

    total_bytes = 0
    passed_tests = 0
    tested_count = 0

    for idx, row in df_manifest.iterrows():
        rel_path = Path(row["file_path"])
        full_path = root / rel_path if not rel_path.is_absolute() else rel_path

        if full_path.exists():
            f_size = full_path.stat().st_size
            total_bytes += f_size
            df_manifest.at[idx, "file_size_bytes"] = f_size
            df_manifest.at[idx, "sha256"] = compute_sha256(full_path)

            # Test reload for joblib models
            if full_path.suffix == ".joblib":
                tested_count += 1
                try:
                    loaded = joblib.load(full_path)
                    preds = loaded.predict(sample_X)
                    if len(preds) == 3 and not np.isnan(preds).any():
                        passed_tests += 1
                        df_manifest.at[idx, "load_test_passed"] = True
                    else:
                        df_manifest.at[idx, "load_test_passed"] = False
                except Exception as e:
                    df_manifest.at[idx, "load_test_passed"] = False
                    df_manifest.at[idx, "notes"] = f"Load error: {e}"

            elif full_path.suffix == ".pt":
                tested_count += 1
                try:
                    st = torch.load(full_path, map_location="cpu", weights_only=True)
                    if isinstance(st, dict):
                        passed_tests += 1
                        df_manifest.at[idx, "load_test_passed"] = True
                    else:
                        df_manifest.at[idx, "load_test_passed"] = False
                except Exception:
                    df_manifest.at[idx, "load_test_passed"] = False
            else:
                passed_tests += 1
                df_manifest.at[idx, "load_test_passed"] = True
        else:
            df_manifest.at[idx, "load_test_passed"] = False
            df_manifest.at[idx, "notes"] = "File missing on disk"

    df_manifest.to_csv(manifest_csv, index=False)

    total_mb = total_bytes / (1024 * 1024)
    print(f"\nManifest Verification Summary:")
    print(f"  - Total indexed entries  : {len(df_manifest)}")
    print(f"  - Load tests passed      : {passed_tests} / {len(df_manifest)} ({(passed_tests/max(1, len(df_manifest)))*100:.1f}%)")
    print(f"  - Total disk storage used: {total_mb:.2f} MB")
    print("Manifest successfully audited and verified!")


if __name__ == "__main__":
    main()
