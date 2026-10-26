import pandas as pd
import numpy as np

lead = pd.read_csv("experiments/leaderboard.csv")
baselines = ["naive", "drift", "moving_average_4", "moving_average_12", "seasonal_naive_48"]

def get_tier(m):
    # Tier 1: linear/statistical
    if m in ["linear_regression", "ridge", "lasso", "elastic_net", "auto_arima", "sarimax", "holt_winters_ets", "prophet"]:
        return (1, "Linear/Statistical")
    # Tier 2: tree
    elif m in ["lightgbm", "xgboost", "catboost", "random_forest", "extra_trees", "gradient_boosting", "svr"]:
        return (2, "Tree/Kernel")
    # Tier 3: deep
    elif m in ["mlp", "lstm", "gru", "tcn_1d", "nbeats", "transformer", "nhits", "tft_lite"]:
        return (3, "Deep Neural")
    # Tier 4: ensemble
    elif m in ["simple_average_top3", "stacking_meta_learner", "best_per_category"]:
        return (4, "Ensemble")
    return (99, "Unknown")

print("=" * 80)
print("PRE-REGISTERED SELECTION RULE PER HORIZON (leaderboard.csv validation split)")
print("=" * 80)

summary_rows = []

for h in [1, 4, 8, 12]:
    val_df = lead[(lead["horizon"] == h) & (lead["split"] == "validation")].copy()
    val_candidates = val_df[~val_df["model"].isin(baselines)].copy()
    val_candidates["tier_num"] = val_candidates["model"].apply(lambda m: get_tier(m)[0])
    val_candidates["tier_name"] = val_candidates["model"].apply(lambda m: get_tier(m)[1])
    val_candidates = val_candidates.sort_values("MASE").reset_index(drop=True)
    val_candidates["val_rank"] = range(1, len(val_candidates) + 1)
    
    best = val_candidates.iloc[0]
    best_mase = best["MASE"]
    ci_str = str(best["MASE_CI_95"]).strip("[]")
    ci_low, ci_high = [float(x) for x in ci_str.split(",")]
    se = (ci_high - ci_low) / (2 * 1.96)
    band_upper = best_mase + se
    
    val_candidates["in_band"] = val_candidates["MASE"] <= band_upper
    band_df = val_candidates[val_candidates["in_band"]].sort_values(["tier_num", "MASE"]).reset_index(drop=True)
    selected = band_df.iloc[0]
    
    print(f"\nHorizon h={h}:")
    print(f"  Candidate models evaluated: {len(val_candidates)}")
    print(f"  Lowest validation MASE model: {best['model']} (rank {best['val_rank']}, Tier {best['tier_num']} - {best['tier_name']})")
    print(f"  Validation MASE: {best_mase:.4f}, 95% Bootstrap CI: [{ci_low:.4f}, {ci_high:.4f}]")
    print(f"  Bootstrap SE: {se:.4f}")
    print(f"  1-SE Selection Band: [{best_mase:.4f}, {band_upper:.4f}]")
    print("  Eligible models inside 1-SE band:")
    for _, r in band_df.iterrows():
        print(f"    - {r['model']:23s} | Tier {r['tier_num']} ({r['tier_name']:18s}) | val_MASE={r['MASE']:.4f} (val rank {r['val_rank']})")
    print(f"  >> SELECTED MODEL: {selected['model']} (Tier {selected['tier_num']} - {selected['tier_name']}, val_MASE={selected['MASE']:.4f}, val rank {selected['val_rank']})")
    
    summary_rows.append({
        "horizon": h,
        "best_model": best["model"],
        "best_val_mase": best_mase,
        "best_mase_ci": f"[{ci_low:.4f}, {ci_high:.4f}]",
        "bootstrap_se": round(se, 4),
        "band_lower": round(best_mase, 4),
        "band_upper": round(band_upper, 4),
        "n_in_band": len(band_df),
        "selected_model": selected["model"],
        "selected_tier": selected["tier_name"],
        "selected_val_mase": selected["MASE"],
        "selected_val_rank": selected["val_rank"]
    })

df_sum = pd.DataFrame(summary_rows)
print("\n" + "=" * 80)
print("SELECTION SUMMARY TABLE:")
print("=" * 80)
print(df_sum.to_string(index=False))

df_sum.to_csv("results/tables/model_selection_bands.csv", index=False)
print("\nSaved to results/tables/model_selection_bands.csv")
