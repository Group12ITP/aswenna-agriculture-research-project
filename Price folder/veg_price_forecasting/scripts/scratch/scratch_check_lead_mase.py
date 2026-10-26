import pandas as pd
df = pd.read_csv("experiments/leaderboard.csv")
for h in [1, 4, 8, 12]:
    n = df[(df["model"]=="naive") & (df["horizon"]==h) & (df["split"]=="test")].iloc[0]
    l_raw = df[(df["model"]=="lasso") & (df["target_mode"]=="raw_level") & (df["horizon"]==h) & (df["split"]=="test")].iloc[0]
    l_ratio = df[(df["model"]=="lasso") & (df["target_mode"]=="log_ratio") & (df["horizon"]==h) & (df["split"]=="test")].iloc[0]
    print(f"h={h}: Naive MASE={n['MASE']:.4f}, Lasso raw MASE={l_raw['MASE']:.4f}, skill={l_raw['Skill_vs_Naive']:.2f}%, Lasso ratio MASE={l_ratio['MASE']:.4f}, skill={l_ratio['Skill_vs_Naive']:.2f}%")
