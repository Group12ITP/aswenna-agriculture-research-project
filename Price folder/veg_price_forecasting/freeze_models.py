import os
import shutil
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

from src.utils import load_config, set_seeds
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.models.statistical import AutoARIMARollingForecaster

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def freeze_all():
    cfg = load_config()
    set_seeds(42)
    
    models_dir = Path("models")
    frozen_dir = models_dir / "frozen"
    cand_dir = frozen_dir / "candidates"
    cand_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("FREEZING SELECTED AND CANDIDATE MODELS WITH SHA-256 MANIFEST")
    print("=" * 80)
    
    # 1. Copy all candidate models to frozen/candidates/
    candidate_manifest = {}
    for joblib_file in sorted(models_dir.glob("*.joblib")):
        dest = cand_dir / joblib_file.name
        shutil.copy2(joblib_file, dest)
        sha = compute_sha256(dest)
        candidate_manifest[joblib_file.stem] = {
            "file": f"candidates/{dest.name}",
            "sha256": sha,
            "size_bytes": dest.stat().st_size
        }
    print(f"Copied and hashed {len(candidate_manifest)} candidate model files to {cand_dir}")
    
    # 2. Package Selected Models for each horizon
    # h=1: lasso (raw_level)
    # h=4: auto_arima (raw_level)
    # h=8: catboost (log_ratio)
    # h=12: transformer (raw_level)
    
    # Copy lasso_h1
    shutil.copy2(models_dir / "lasso_h1.joblib", frozen_dir / "selected_h1_lasso.joblib")
    
    # Copy catboost_h8
    shutil.copy2(models_dir / "catboost_h8.joblib", frozen_dir / "selected_h8_catboost.joblib")
    
    # Copy transformer_h12
    shutil.copy2(models_dir / "transformer_h12.joblib", frozen_dir / "selected_h12_transformer.joblib")
    
    # Build and save selected h=4 auto_arima on all 464 weeks
    print("Fitting AutoARIMA models across all 32 vegetables on full 464-week history...")
    _, df_long = load_and_preprocess_vegetables(cfg)
    auto_arima_models = {}
    for veg in df_long["product_name"].unique():
        v_df = df_long[df_long["product_name"] == veg].sort_values("week_index")
        prices = v_df["price_lkr"].values
        forecaster = AutoARIMARollingForecaster(d=1)
        forecaster.fit_parameters(prices)
        auto_arima_models[veg] = {
            "order": forecaster.best_order,
            "d": forecaster.d,
            "fitted_aic": getattr(forecaster.fitted_res, "aic", None) if forecaster.fitted_res else None
        }
    
    arima_path = frozen_dir / "selected_h4_auto_arima.joblib"
    joblib.dump(auto_arima_models, arima_path)
    print(f"Saved selected AutoARIMA suite to {arima_path}")
    
    # Conformal multipliers per category
    conformal_quantiles = {
        "leafy vegetables": {"q_80": 0.0814, "mult_lower": 0.922, "mult_upper": 1.085, "width_pct": 16.3},
        "lowland vegetables": {"q_80": 0.2696, "mult_lower": 0.764, "mult_upper": 1.309, "width_pct": 54.6},
        "upcountry vegetables": {"q_80": 0.3769, "mult_lower": 0.686, "mult_upper": 1.458, "width_pct": 77.2}
    }
    
    selected_models_manifest = {
        "h1": {
            "model": "lasso",
            "target_mode": "raw_level",
            "tier": "Linear/Statistical",
            "file": "selected_h1_lasso.joblib",
            "sha256": compute_sha256(frozen_dir / "selected_h1_lasso.joblib"),
            "training_range": "Weeks 1 to 464 (2017-01-04 to 2026-08-25)",
            "hyperparameters": {"alpha": 1.5359, "fit_intercept": True, "standardize": True},
            "seed": 42
        },
        "h4": {
            "model": "auto_arima",
            "target_mode": "raw_level",
            "tier": "Linear/Statistical",
            "file": "selected_h4_auto_arima.joblib",
            "sha256": compute_sha256(arima_path),
            "training_range": "Weeks 1 to 464 (2017-01-04 to 2026-08-25)",
            "hyperparameters": {"d": 1, "order_search": [(1,1,0), (0,1,1), (1,1,1), (2,1,1)]},
            "seed": 42,
            "conformal_calibration": conformal_quantiles
        },
        "h8": {
            "model": "catboost",
            "target_mode": "log_ratio",
            "tier": "Tree/Ensemble ML",
            "file": "selected_h8_catboost.joblib",
            "sha256": compute_sha256(frozen_dir / "selected_h8_catboost.joblib"),
            "training_range": "Weeks 1 to 464 (2017-01-04 to 2026-08-25)",
            "hyperparameters": {"iterations": 300, "depth": 6, "learning_rate": 0.05},
            "seed": 42
        },
        "h12": {
            "model": "transformer",
            "target_mode": "raw_level",
            "tier": "Deep Learning",
            "file": "selected_h12_transformer.joblib",
            "sha256": compute_sha256(frozen_dir / "selected_h12_transformer.joblib"),
            "training_range": "Weeks 1 to 464 (2017-01-04 to 2026-08-25)",
            "hyperparameters": {"d_model": 64, "nhead": 4, "num_layers": 2, "dropout": 0.1},
            "seed": 42
        }
    }
    
    full_manifest = {
        "manifest_version": "1.0.0",
        "created_at": "2026-10-05T11:45:00",
        "dataset": "Sri Lankan Weekly Vegetable Market Prices",
        "frozen_training_end_week": 464,
        "frozen_training_end_date": "2026-08-25",
        "holdout_start_date": "2026-09-04",
        "selected_models": selected_models_manifest,
        "candidate_models_count": len(candidate_manifest),
        "candidates": candidate_manifest
    }
    
    manifest_file = frozen_dir / "frozen_model_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(full_manifest, f, indent=2)
        
    print(f"\nSaved frozen model manifest to {manifest_file}")
    for h_key, s_info in selected_models_manifest.items():
        print(f"  {h_key}: {s_info['model']} ({s_info['target_mode']}) -> {s_info['file']} [SHA: {s_info['sha256'][:16]}...]")

if __name__ == "__main__":
    freeze_all()
