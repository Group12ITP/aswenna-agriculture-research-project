import pandas as pd

df_lead = pd.read_csv('experiments/leaderboard.csv')
for h in [1, 4]:
    r = df_lead[(df_lead['horizon'] == h) & (df_lead['split'] == 'validation') & (df_lead['model'] == 'naive')].iloc[0]
    scale = r['MAE'] / r['MASE']
    print(f"h={h}: Leaderboard Naive MAE = {r['MAE']}, MASE = {r['MASE']}, implied scale = {scale:.4f}")
