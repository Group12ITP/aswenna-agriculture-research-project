import pandas as pd
df = pd.read_csv('experiments/leaderboard.csv')
h4_test = df[(df['horizon']==4) & (df['split']=='test')]
print("h=4 test rows:", len(h4_test))
counts = h4_test['model'].value_counts()
dups = counts[counts > 1].index.tolist()
print("Models with both modes:", dups)
print("Unique models count:", len(counts))
