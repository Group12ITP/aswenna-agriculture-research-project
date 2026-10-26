import pandas as pd
import numpy as np

lead = pd.read_csv("experiments/leaderboard.csv")
by_veg = pd.read_csv("experiments/leaderboard_by_vegetable.csv")

print("=== SELECTION RULE ANALYSIS AT h=4 ===")
h4_veg = by_veg[by_veg["horizon"] == 4]
val_h4 = h4_veg.groupby("model")["val_MASE"].agg(["median", "mean", "std", "count"]).reset_index()
val_h4["se"] = val_h4["std"] / np.sqrt(val_h4["count"])
val_h4 = val_h4.sort_values("median").reset_index(drop=True)

best = val_h4.iloc[0]
best_median = best["median"]
best_se = best["se"]
threshold = best_median + best_se

print(f"Best model on validation median MASE: [{best['model']}] with median = {best_median:.4f}, SE = {best_se:.4f}")
print(f"1-SE threshold: {threshold:.4f}\n")

def model_complexity(m):
    if m in ["linear_regression", "ridge", "lasso", "elastic_net"]:
        return (1, "linear")
    elif m in ["lightgbm", "xgboost", "catboost", "random_forest", "extra_trees", "gradient_boosting", "svr"]:
        return (2, "tree/kernel")
    elif m in ["mlp", "lstm", "gru", "tcn_1d", "nbeats", "transformer", "nhits", "tft_lite"]:
        return (3, "deep")
    elif m in ["auto_arima", "sarimax", "holt_winters_ets", "prophet", "naive", "seasonal_naive_48", "moving_average_4", "moving_average_12", "drift"]:
        return (0, "statistical/baseline")
    else:
        return (4, "ensemble")

val_h4["rank_comp"] = val_h4["model"].apply(lambda m: model_complexity(m)[0])
val_h4["comp_family"] = val_h4["model"].apply(lambda m: model_complexity(m)[1])
val_h4["within_1se"] = val_h4["median"] <= threshold

print(val_h4.to_string())

eligible = val_h4[val_h4["within_1se"]].sort_values(by=["rank_comp", "median"])
print("\nEligible models within 1-SE (sorted by simplicity hierarchy):")
print(eligible[["model", "comp_family", "median", "se"]].to_string())

chosen_one_se = eligible.iloc[0]["model"]
print(f"\nWinning Model by 1-SE Simplicity Rule: [{chosen_one_se}]")
print(f"Absolute Lowest Median Validation MASE Model: [{best['model']}]")

print("\n=== LOWEST MEDIAN VALIDATION MASE FOR EACH HORIZON ===")
for h in [1, 4, 8, 12]:
    h_sub = by_veg[by_veg["horizon"] == h].groupby("model")["val_MASE"].agg(["median", "std", "count"]).reset_index()
    h_sub["se"] = h_sub["std"] / np.sqrt(h_sub["count"])
    h_sub["rank_comp"] = h_sub["model"].apply(lambda m: model_complexity(m)[0])
    h_sub["comp_family"] = h_sub["model"].apply(lambda m: model_complexity(m)[1])
    h_sub = h_sub.sort_values("median").reset_index(drop=True)
    b_m = h_sub.iloc[0]["median"]
    b_se = h_sub.iloc[0]["se"]
    thresh = b_m + b_se
    elig = h_sub[h_sub["median"] <= thresh].sort_values(by=["rank_comp", "median"])
    print(f"h={h:2d}: Best Median = [{h_sub.iloc[0]['model']:22s}] ({b_m:.4f}) | 1-SE Chosen = [{elig.iloc[0]['model']:22s}] ({elig.iloc[0]['median']:.4f})")
