import pandas as pd
df = pd.read_csv("experiments/leaderboard_by_category.csv")
sub = df[(df["horizon"] == 4) & (df["category"] == "leafy vegetables")]
print(sub.to_string(index=False))
