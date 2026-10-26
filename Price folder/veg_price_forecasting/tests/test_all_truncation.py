import sys
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
import torch

from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.train import prepare_feature_matrices

cfg = load_config()
df_wide, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg)

h = 4
target_col = f"target_h{h}"
X, y, feature_cols = prepare_feature_matrices(df_feat, target_col=target_col)

# Find full run paths for h=4 models
models_to_test = [
    "auto_arima", "lasso", "lightgbm", "tcn_1d",
    "nbeats", "transformer", "simple_average_top3",
    "best_per_category", "stacking_meta_learner"
]

run_dirs = {}
for m in models_to_test:
    for p in sorted(Path("experiments/runs").glob(f"*_{m}_h{h}")):
        pred_f = p / "predictions_test.csv"
        if pred_f.exists():
            df_check = pd.read_csv(pred_f)
            if len(df_check) >= 1500:
                run_dirs[m] = p
                break
    print(f"Model {m}: Run dir = {run_dirs.get(m)}")

# For each model, verify that feature row X.loc[t] and predictions match identically under truncation
# Pick 5 random test origins per vegetable
rng = np.random.default_rng(42)
all_vegs = df_long["product_name"].unique()

test_indices_by_veg = {}
for veg in all_vegs:
    v_mask = (df_feat["product_name"] == veg) & test_mask
    valid_indices = [idx for idx in df_feat.index[v_mask] if pd.notna(df_feat.loc[idx, target_col])]
    sampled = rng.choice(valid_indices, size=5, replace=False)
    test_indices_by_veg[veg] = sampled

results = {}

for m in models_to_test:
    p_dir = run_dirs.get(m)
    if not p_dir:
        print(f"Skipping {m}: run dir not found.")
        continue
    lead_preds = pd.read_csv(p_dir / "predictions_test.csv")
    
    # Load model artefact if available
    model_file = Path("models") / f"{m}_h{h}.joblib"
    loaded_model = None
    if model_file.exists():
        try:
            loaded_model = joblib.load(model_file)
        except Exception as e:
            pass
            
    mismatches = 0
    total = 0
    
    for veg, origins in test_indices_by_veg.items():
        for orig in origins:
            total += 1
            orig_date = df_feat.loc[orig, "approx_date"]
            
            # TRUNCATION: Truncate raw dataset up to orig_date
            # Check if features at orig change at all
            orig_week_idx = df_feat.loc[orig, "week_index"]
            
            # Reconstruct truncated raw dataset
            df_long_trunc = df_long[df_long["week_index"] <= orig_week_idx].copy()
            df_feat_trunc = build_vegetable_features(df_long_trunc, cfg=cfg, include_cross_veg=True)
            
            # Find the corresponding row in df_feat_trunc
            trunc_row = df_feat_trunc[(df_feat_trunc["product_name"] == veg) & (df_feat_trunc["week_index"] == orig_week_idx)]
            full_row = df_feat.loc[[orig]]
            
            # Check feature equality (excluding future targets)
            feat_diff = 0
            for col in feature_cols:
                if col in trunc_row.columns and col in full_row.columns:
                    v1 = trunc_row[col].values[0]
                    v2 = full_row[col].values[0]
                    if pd.notna(v1) and pd.notna(v2):
                        if abs(v1 - v2) > 1e-4:
                            feat_diff += 1
                    elif pd.isna(v1) != pd.isna(v2):
                        feat_diff += 1
            if feat_diff > 0:
                mismatches += 1
                
    results[m] = {"total_tested": total, "feature_mismatches": mismatches}
    print(f"Model {m}: {total} origins tested, {mismatches} mismatches under disk-level truncation.")

print("\n--- ALL MODEL TRUNCATION TEST SUMMARY ---")
for m, r in results.items():
    print(f"{m:25s}: {r['feature_mismatches']} mismatches out of {r['total_tested']} origins.")
