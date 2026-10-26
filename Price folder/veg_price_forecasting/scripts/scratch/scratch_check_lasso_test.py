import pandas as pd
df = pd.read_csv("experiments/leaderboard.csv")
sub = df[(df["model"]=="lasso") & (df["target_mode"]=="raw_level") & (df["split"]=="test")]
print(sub[["horizon", "MAE", "MASE", "R2", "Skill_vs_Naive"]].to_string(index=False))
