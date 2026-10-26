import pandas as pd
df = pd.read_csv('experiments/leaderboard.csv')
for h in [1, 4, 8, 12]:
    row = df[(df['split']=='test') & (df['model']=='naive') & (df['horizon']==h)].iloc[0]
    mae = row['MAE']
    mase = row['MASE']
    scale = mae / mase
    print(f"h={h}: n={row['n_obs']}, MAE={mae:.4f}, MASE={mase:.4f}, scale={scale:.4f}")
