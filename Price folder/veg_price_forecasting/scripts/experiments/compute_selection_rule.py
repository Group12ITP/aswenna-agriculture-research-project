import pandas as pd
import numpy as np

lead = pd.read_csv("experiments/leaderboard.csv")
by_veg = pd.read_csv("experiments/leaderboard_by_vegetable.csv")

baselines = ["naive", "drift", "moving_average_4", "moving_average_12", "seasonal_naive_48"]

def get_tier(m):
    # Tier 1: linear/statistical
    if m in ["linear_regression", "ridge", "lasso", "elastic_net", "auto_arima", "sarimax", "holt_winters_ets", "prophet"]:
        return (1, "linear/statistical")
    # Tier 2: tree
    elif m in ["lightgbm", "xgboost", "catboost", "random_forest", "extra_trees", "gradient_boosting", "svr"]:
        return (2, "tree")
    # Tier 3: deep
    elif m in ["mlp", "lstm", "gru", "tcn_1d", "nbeats", "transformer", "nhits", "tft_lite"]:
        return (3, "deep")
    # Tier 4: ensemble
    elif m in ["simple_average_top3", "stacking_meta_learner", "best_per_category"]:
        return (4, "ensemble")
    return (99, "unknown")

print("=" * 60)
print("METHOD 1: FROM leaderboard_by_vegetable.csv (Median across vegetables)")
print("=" * 60)
for h in [1, 4, 8, 12]:
    sub = by_veg[by_veg["horizon"] == h].copy()
    sub = sub[~sub["model"].isin(baselines)]
    agg = sub.groupby("model")["val_MASE"].agg(["median", "mean", "std", "count"]).reset_index()
    agg["se"] = agg["std"] / np.sqrt(agg["count"])
    agg["tier"] = agg["model"].apply(lambda m: get_tier(m)[0])
    agg["tier_name"] = agg["model"].apply(lambda m: get_tier(m)[1])
    agg = agg.sort_values("median").reset_index(drop=True)
    
    best = agg.iloc[0]
    best_m = best["median"]
    best_se = best["se"]
    thresh = best_m + best_se
    
    in_band = agg[agg["median"] <= thresh].sort_values(["tier", "median"]).reset_index(drop=True)
    chosen = in_band.iloc[0]
    
    print(f"\nHorizon h={h}:")
    print(f"  Best Model: {best['model']} (Tier: {best['tier_name']}, Median: {best_m:.4f}, SE: {best_se:.4f})")
    print(f"  1-SE Band: [{best_m:.4f}, {thresh:.4f}]")
    print("  Models in Band:")
    for _, r in in_band.iterrows():
        print(f"    - {r['model']:25s} | Tier {r['tier']} ({r['tier_name']:18s}) | Median: {r['median']:.4f}")
    print(f"  --> SELECTED: {chosen['model']} (Tier {chosen['tier']} - {chosen['tier_name']}, Median: {chosen['median']:.4f})")

print("\n" + "=" * 60)
print("METHOD 2: Using bootstrap CIs from validation split")
print("=" * 60)
for h in [1, 4, 8, 12]:
    sub_veg = by_veg[by_veg["horizon"] == h].copy()
    sub_veg = sub_veg[~sub_veg["model"].isin(baselines)]
    agg = sub_veg.groupby("model")["val_MASE"].agg(["median", "count"]).reset_index()
    
    # Get bootstrap CI from leaderboard.csv
    val_lead = lead[(lead["horizon"] == h) & (lead["split"] == "validation")].set_index("model")
    
    agg["val_MASE_pooled"] = agg["model"].apply(lambda m: val_lead.loc[m, "MASE"] if m in val_lead.index else np.nan)
    agg["ci_str"] = agg["model"].apply(lambda m: str(val_lead.loc[m, "MASE_CI_95"]) if m in val_lead.index else "")
    
    def parse_se(s):
        try:
            low, high = [float(x) for x in s.strip("[]").split(",")]
            return (high - low) / (2 * 1.96)
        except:
            return 0.05
            
    agg["se_boot"] = agg["ci_str"].apply(parse_se)
    agg["tier"] = agg["model"].apply(lambda m: get_tier(m)[0])
    agg["tier_name"] = agg["model"].apply(lambda m: get_tier(m)[1])
    
    # Option 2A: sort by median val_MASE, use se_boot of best
    agg_sort = agg.sort_values("median").reset_index(drop=True)
    best_m = agg_sort.iloc[0]["median"]
    best_se = agg_sort.iloc[0]["se_boot"]
    thresh = best_m + best_se
    in_band = agg_sort[agg_sort["median"] <= thresh].sort_values(["tier", "median"]).reset_index(drop=True)
    chosen = in_band.iloc[0]
    
    print(f"\nHorizon h={h} (Median with boot SE):")
    print(f"  Best Model: {agg_sort.iloc[0]['model']} (Median: {best_m:.4f}, Boot SE: {best_se:.4f}, Band: [{best_m:.4f}, {thresh:.4f}])")
    print(f"  --> SELECTED: {chosen['model']} (Tier {chosen['tier']} - {chosen['tier_name']}, Median: {chosen['median']:.4f})")
