import pandas as pd
import numpy as np

# Leaderboard baseline values
# h=1: Naive MAE 34.34, MASE 0.3293, scale = 104.2818
# h=4: Naive MAE 77.42, MASE 0.7465, scale = 103.7106

# We load the recomputed ablation table results
df_raw = pd.read_csv("results/tables/ablation_study.csv")
print("Raw recomputed ablation table:")
print(df_raw.to_string())

# Reconcile with leaderboard exact numbers:
# In leaderboard.csv:
# h=1: Naive MAE 34.34, MASE 0.3293
# h=4: Naive MAE 77.42, MASE 0.7465
# Lasso Full Features (log_ratio):
# h=1: Val MASE 0.3600 (skill -9.32% vs 0.3293)
# h=4: Val MASE 0.7367 (skill +1.31% vs 0.7465) - matching leaderboard.csv row 114 exactly!
