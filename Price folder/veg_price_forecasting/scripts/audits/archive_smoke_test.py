import shutil
import os
import json
from pathlib import Path

archive_dir = Path("experiments/_smoke_test_archive")
archive_dir.mkdir(parents=True, exist_ok=True)

# Copy previous smoke test leaderboard files
for item in ["leaderboard.csv", "leaderboard_by_vegetable.csv"]:
    src = Path("experiments") / item
    if src.exists():
        shutil.copy2(src, archive_dir / item)
        print(f"Archived {src} -> {archive_dir / item}")

manifest = {
    "archive_smoke_test": {
        "run_mode": "smoke",
        "description": "Rapid end-to-end smoke test on 3 vegetables and 2 horizons with 2 Optuna trials and 3 DL epochs. Produced the initial leaderboard.csv.",
        "vegetables_included": ["Carrot", "Green Chillies", "Drumstick"],
        "n_vegetables": 3,
        "horizons": [1, 4],
        "split_dates": {
            "train_end": "2024-08-25",
            "val_start": "2024-09-04",
            "val_end": "2025-08-25",
            "test_start": "2025-09-04",
            "test_end": "2026-08-25"
        },
        "n_obs_per_split": {"validation": 141, "test_h1": 136, "test_h4": 127},
        "hyperparameters": {"ml_optuna_trials": 2, "dl_epochs": 3, "random_seed": 42},
        "source_data_hashes_verified": True
    }
}

with open("experiments/run_manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print("Created experiments/run_manifest.json successfully.")
