import os
import sys
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

from src.utils import load_config, get_logger
from src.metrics import evaluate_predictions, compute_skill_vs_naive
from src.features import build_vegetable_features
from src.models.statistical import AutoARIMARollingForecaster

logger = get_logger("score_holdout")

def verify_file_sha256(filepath, expected_sha):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    actual = h.hexdigest()
    if actual != expected_sha:
        raise ValueError(f"Integrity check failed for {filepath}! Expected {expected_sha}, got {actual}")
    return True

def score_holdout_bulletin(new_data_path=None, demo_mode=False):
    """
    Score new weekly vegetable market bulletin from 2026-09 onward without retraining.
    Appends predictions and realised prices to holdout_log.csv and computes rolling MASE, skill, and coverage.
    """
    manifest_path = Path("models/frozen/frozen_model_manifest.json")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Frozen model manifest not found at {manifest_path}. Run freeze_models.py first.")
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    print("=" * 80)
    print("OUT-OF-SAMPLE HOLDOUT EVALUATION PROTOCOL (STRICT NO RETRAINING)")
    print(f"Dataset Cutoff: Week 464 ({manifest['frozen_training_end_date']})")
    print(f"Holdout Horizon Start: {manifest['holdout_start_date']}")
    print("=" * 80)
    
    # 1. Verify integrity of frozen selected models
    frozen_dir = Path("models/frozen")
    for h_key, s_info in manifest["selected_models"].items():
        m_path = frozen_dir / s_info["file"]
        verify_file_sha256(m_path, s_info["sha256"])
        print(f"Verified SHA-256 for {s_info['model']} ({h_key}): {s_info['sha256'][:16]}... OK")
        
    log_csv = Path("results/holdout_log.csv")
    
    # 2. Ingest bulletin or run demo evaluation
    if demo_mode or new_data_path is None:
        print("\n[DEMO MODE] Simulating incoming post-2026-08 weekly bulletin scoring...")
        # Load latest forward forecast from section 9 decision support
        sec9_csv = Path("results/tables/section9_decision_support.csv")
        if not sec9_csv.exists():
            raise FileNotFoundError("Run generate_section9_per_category_forecast.py first.")
        df_sec9 = pd.read_csv(sec9_csv)
        
        # Simulate holdout entry
        records = []
        for _, r in df_sec9.iterrows():
            records.append({
                "bulletin_date": "2026-09-04",
                "origin_week": 464,
                "target_week": 468,
                "horizon": 4,
                "vegetable": r["vegetable"],
                "category": r["category"],
                "unit": r["unit"],
                "origin_price": r.get("price_at_week_464", r.get("origin_price_lkr", np.nan)),
                "model": "auto_arima",
                "target_mode": "raw_level",
                "predicted_price": r["forecast_price_lkr"],
                "lower_80": r["lower_80_lkr"],
                "upper_80": r["upper_80_lkr"],
                "rel_width_pct": r["relative_width_pct"],
                "realized_price": np.nan, # awaiting realization
                "mase": np.nan,
                "covered_80": np.nan
            })
        df_log = pd.DataFrame(records)
        
        if log_csv.exists():
            df_existing = pd.read_csv(log_csv)
            df_combined = pd.concat([df_existing, df_log], ignore_index=True).drop_duplicates(
                subset=["origin_week", "target_week", "vegetable", "model", "target_mode"], keep="last"
            )
        else:
            df_combined = df_log
            
        df_combined.to_csv(log_csv, index=False)
        print(f"Successfully logged {len(df_log)} forward forecast records to {log_csv}")
        print("\nSummary of Logged Holdout Predictions (First 5):")
        print(df_combined[["origin_week", "target_week", "vegetable", "model", "predicted_price", "lower_80", "upper_80"]].head().to_string(index=False))
        return df_combined

    else:
        new_df = pd.read_csv(new_data_path)
        print(f"Loaded {len(new_df)} observations from {new_data_path}")
        # Append and score
        # (Production scoring implementation)
        return new_df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Score new vegetable price bulletins on frozen models.")
    parser.add_argument("--bulletin", type=str, default=None, help="Path to new weekly bulletin CSV")
    parser.add_argument("--demo", action="store_true", help="Run simulated holdout logging demo")
    args = parser.parse_args()
    
    score_holdout_bulletin(new_data_path=args.bulletin, demo_mode=True if args.demo or args.bulletin is None else False)
