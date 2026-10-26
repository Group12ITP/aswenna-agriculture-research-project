import pandas as pd
df = pd.read_csv('experiments/leaderboard.csv')
for h in [1, 4, 8, 12]:
    sub = df[(df['split']=='test') & (df['horizon']==h) & (df['model'].isin(['naive', 'auto_arima', 'sarimax', 'prophet']))]
    print(f"--- Horizon h={h} ---")
    print(sub[['model', 'n_obs', 'MAE', 'MASE', 'Skill_vs_Naive', 'DM_stat_vs_Naive', 'DM_pval_vs_Naive', 'DM_pval_Holm_vs_Naive']])
