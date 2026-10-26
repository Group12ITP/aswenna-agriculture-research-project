import sys
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
train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg, horizon=h)

# Evaluation on test split
target_col = f"target_h{h}"
y_true = df_feat.loc[test_mask, target_col]
is_leafy = (df_feat.loc[test_mask, "category"] == "leafy vegetables")
is_clean = (df_feat.loc[test_mask, "is_stale_run"] == 0.0)

# Clean leafy mask
mask_all_leafy = is_leafy
mask_clean_leafy = is_leafy & is_clean

print(f"Leafy test observations: Total = {mask_all_leafy.sum()}, Clean = {mask_clean_leafy.sum()}, Stale = {(mask_all_leafy & ~is_clean).sum()}")

runs_dir = Path("experiments/runs")
models = [
    "naive", "seasonal_naive_48", "moving_average_4", "drift",
    "auto_arima", "sarimax", "prophet", "lasso", "ridge", "elastic_net",
    "random_forest", "extra_trees", "lightgbm", "xgboost", "catboost",
    "mlp", "lstm", "gru", "tcn_1d", "transformer", "tft_lite",
    "simple_average_top3", "stacking_meta_learner", "best_per_category"
]

rows = []
for m in models:
    matches = sorted(runs_dir.glob(f"*_{m}_h{h}"))
    valid = [p for p in matches if (p / "predictions_test.csv").exists() and len(pd.read_csv(p / "predictions_test.csv")) >= 1400]
    if not valid:
        continue
    latest = valid[-1]
    df_p = pd.read_csv(latest / "predictions_test.csv")
    y_pred = pd.Series(df_p["y_pred"].values, index=y_true.index)
    
    # All leafy
    m_all = evaluate_predictions(y_true[mask_all_leafy], y_pred[mask_all_leafy])
    # Clean leafy
    m_clean = evaluate_predictions(y_true[mask_clean_leafy], y_pred[mask_clean_leafy])
    
    rows.append({
        "model": m,
        "all_MAE": m_all["MAE"],
        "all_sMAPE": m_all["sMAPE"],
        "all_R2": m_all["R2"],
        "clean_MAE": m_clean["MAE"],
        "clean_sMAPE": m_clean["sMAPE"],
        "clean_R2": m_clean["R2"]
    })

df_out = pd.DataFrame(rows)
df_out.to_csv("results/tables/leafy_stale_vs_clean.csv", index=False)
print("\n=== LEAFY VEGETABLES: STALE VS CLEAN AUDIT (h=4) ===")
print(df_out.to_string(index=False))
