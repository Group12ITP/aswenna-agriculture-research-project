import pandas as pd

df = pd.read_csv("experiments/leaderboard.csv")
baselines = ['naive', 'drift', 'moving_average_4', 'moving_average_12', 'seasonal_naive_48']

for h in [1, 4, 8, 12]:
    sub = df[(df['horizon'] == h) & (df['split'] == 'test')]
    cands = sub[~sub['model'].isin(baselines)]
    better = cands[cands['Skill_vs_Naive'] > 0]
    sig_better = better[better['DM_pval_Holm_vs_Naive'] < 0.05]
    all_sig = cands[cands['DM_pval_Holm_vs_Naive'] < 0.05]
    print(f"Horizon h={h}: Total rows={len(sub)}, Candidates={len(cands)}, Better than naive={len(better)}, Holm sig better={len(sig_better)}, Any Holm sig={len(all_sig)}")
    if len(all_sig) > 0:
        for _, r in all_sig.iterrows():
            print(f"   Model: {r['model']} ({r['target_mode']}), Skill: {r['Skill_vs_Naive']:.2f}%, Holm-p: {r['DM_pval_Holm_vs_Naive']:.4f}")
