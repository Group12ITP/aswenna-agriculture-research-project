import pandas as pd
df = pd.read_csv('experiments/leaderboard.csv')
h1 = df[(df['split']=='test') & (df['horizon']==1) & (df['model']!='naive')]
worse = h1[(h1['DM_pval_Holm_vs_Naive'] < 0.05) & (h1['Skill_vs_Naive'] < 0)]
print(f'Total h=1 non-naive models in leaderboard: {len(h1)}')
print(f'Total significantly worse at h=1: {len(worse)}')
for _, r in worse.iterrows():
    print(f"  {r['model']} ({r['target_mode']}): skill={r['Skill_vs_Naive']:+.2f}%, holm_p={r['DM_pval_Holm_vs_Naive']:.4f}")
