import json
from pathlib import Path
import numpy as np
import pandas as pd

from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.metrics import evaluate_predictions

cfg = load_config()
df_wide, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)

h = 4
target_col = f"target_h{h}"
train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg, horizon=h)

# Leafy test set
is_leafy = (df_feat["category"] == "leafy vegetables")
leafy_test_mask = test_mask & is_leafy

# Stale vs clean on test
stale_mask = (df_feat["is_stale_run"] == 1.0)
clean_mask = (df_feat["is_stale_run"] == 0.0)

n_total = leafy_test_mask.sum()
n_clean = (leafy_test_mask & clean_mask).sum()
n_stale = (leafy_test_mask & stale_mask).sum()

print(f"Leafy test sample (h={h}): Total={n_total}, Clean={n_clean}, Stale={n_stale}")

# Get all predictions from leaderboard runs or test predictions
# Let's inspect test predictions for models at h=4
y_true_leafy = df_feat.loc[leafy_test_mask, target_col].values
y_orig_leafy = df_feat.loc[leafy_test_mask, "price_lkr"].values
y_hist = df_feat.loc[train_mask | val_mask, "price_lkr"].values

# 1. Naive baseline
naive_mets = evaluate_predictions(y_true_leafy, y_orig_leafy, y_train_history=y_hist)
print(f"Naive: MAE={naive_mets['MAE']:.2f}, sMAPE={naive_mets['sMAPE']:.2f}%, R2={naive_mets['R2']:.4f}")

# Check per_category_h4_summary.csv models
cat_summary = pd.read_csv("results/tables/per_category_h4_summary.csv")
cat_leafy = cat_summary[cat_summary["category"] == "leafy vegetables"]
print("\nFrom per_category_h4_summary.csv:")
print(cat_leafy[["model", "test_MAE", "test_sMAPE", "test_MASE", "test_R2"]])

# Check runs in experiments/runs
runs_dir = Path("experiments/runs")
models = [
    "naive", "auto_arima", "best_per_category", "extra_trees", 
    "lightgbm", "tcn_1d", "lasso", "simple_average_top3", "gru"
]
