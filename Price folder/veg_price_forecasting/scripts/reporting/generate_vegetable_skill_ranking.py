import pandas as pd
import numpy as np
from pathlib import Path
from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.splits import get_split_masks

cfg = load_config()
_, df_long = load_and_preprocess_vegetables(cfg)
_, _, test_mask = get_split_masks(df_long, cfg, horizon=4)
te_df = df_long[test_mask]
veg_stats = te_df.groupby("product_name")["price_lkr"].agg(["std", "mean"]).reset_index()
veg_stats["cv"] = (veg_stats["std"] / veg_stats["mean"]).round(3)
veg_stats = veg_stats.set_index("product_name")

by_veg = pd.read_csv("experiments/leaderboard_by_vegetable.csv")
h4_veg = by_veg[by_veg["horizon"] == 4].copy()
naive = h4_veg[h4_veg["model"] == "naive"].set_index("vegetable")

for model in ["auto_arima", "lasso"]:
    m_veg = h4_veg[h4_veg["model"] == model].set_index("vegetable")
    if m_veg.empty:
        continue
    df_rank = pd.DataFrame(index=m_veg.index)
    df_rank["test_MAE"] = m_veg["test_MAE"].round(2)
    df_rank["test_sMAPE"] = m_veg["test_sMAPE"].round(2)
    df_rank["test_MASE"] = m_veg["test_MASE"].round(4)
    df_rank["naive_MASE"] = naive["test_MASE"].round(4)
    df_rank["test_R2"] = m_veg["test_R2"].round(4)
    df_rank["skill_vs_naive"] = ((1.0 - df_rank["test_MASE"] / df_rank["naive_MASE"]) * 100.0).round(2)
    df_rank["test_std"] = veg_stats["std"].round(2)
    df_rank["is_low_variance"] = df_rank["test_std"] < 15.0
    df_sorted = df_rank.sort_values("skill_vs_naive", ascending=False)
    out_path = f"results/tables/vegetable_skill_ranking_{model}_h4.csv"
    df_sorted.to_csv(out_path)
    print(f"Saved {model} ranking to {out_path} ({len(df_sorted)} vegetables)")
