import pandas as pd
import numpy as np

df = pd.read_csv("experiments/leaderboard.csv")
val = df[df["split"] == "validation"].copy()

baselines = ["naive", "drift", "moving_average_4", "moving_average_12", "seasonal_naive_48"]
val_non_base = val[~val["model"].isin(baselines)]

print("Top 10 Validation models per horizon:")
for h in [1, 4, 8, 12]:
    sub = val_non_base[val_non_base["horizon"] == h].sort_values("MASE")
    print(f"\n--- Horizon h={h} ---")
    print(sub[["model", "target_mode", "MASE", "sMAPE", "Bias"]].head(10).to_string(index=False))

print("\nModel Selection Bands Table:")
df_bands = pd.read_csv("results/tables/model_selection_bands.csv")
print(df_bands.to_string(index=False))
