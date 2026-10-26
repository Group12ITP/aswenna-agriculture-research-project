import pandas as pd

df = pd.read_csv("experiments/leaderboard.csv")
p = df[df["model"] == "prophet"]
cols = ["horizon", "split", "MAE", "RMSE", "sMAPE", "MASE", "R2", "Bias", "Skill_vs_Naive", "DM_stat_vs_Naive", "DM_pval_vs_Naive", "DM_pval_Holm_vs_Naive"]
print(p[cols].to_string(index=False))
