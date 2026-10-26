import pandas as pd

df_old = pd.read_csv("experiments/leaderboard_old.csv")
df_new = pd.read_csv("experiments/leaderboard.csv")

# Filter for key representative models at primary horizon h=4 test split
models = ["naive", "auto_arima", "prophet", "lasso", "ridge", "elastic_net", "lightgbm", "catboost", "extra_trees", "gru", "tcn_1d", "transformer", "simple_average_top3", "best_per_category"]

print("="*95)
print("OLD (Origin-Date Split) VS NEW (Target-Date Split) LEADERBOARD COMPARISON (h=4, Test Split)")
print("="*95)
header = f"{'Model':<22} | {'Old Val MASE':<12} | {'New Val MASE':<12} | {'Old Test MASE':<13} | {'New Test MASE':<13} | {'Old Skill':<10} | {'New Skill':<10}"
print(header)
print("-" * len(header))

for m in models:
    # Old
    o_val = df_old[(df_old['horizon'] == 4) & (df_old['split'] == 'validation') & (df_old['model'] == m)]
    o_tst = df_old[(df_old['horizon'] == 4) & (df_old['split'] == 'test') & (df_old['model'] == m)]
    
    # New (prefer raw_level for direct comparison, or log_ratio if specified)
    n_val = df_new[(df_new['horizon'] == 4) & (df_new['split'] == 'validation') & (df_new['model'] == m)]
    n_tst = df_new[(df_new['horizon'] == 4) & (df_new['split'] == 'test') & (df_new['model'] == m)]
    
    # pick raw_level if multiple
    if len(n_val) > 1:
        n_val = n_val[n_val['target_mode'] == 'raw_level']
    if len(n_tst) > 1:
        n_tst = n_tst[n_tst['target_mode'] == 'raw_level']
        
    ov_m = f"{o_val['MASE'].iloc[0]:.4f}" if len(o_val) > 0 else "N/A"
    nv_m = f"{n_val['MASE'].iloc[0]:.4f}" if len(n_val) > 0 else "N/A"
    ot_m = f"{o_tst['MASE'].iloc[0]:.4f}" if len(o_tst) > 0 else "N/A"
    nt_m = f"{n_tst['MASE'].iloc[0]:.4f}" if len(n_tst) > 0 else "N/A"
    
    os_k = f"{o_tst['Skill_vs_Naive'].iloc[0]:.2f}%" if len(o_tst) > 0 else "N/A"
    ns_k = f"{n_tst['Skill_vs_Naive'].iloc[0]:.2f}%" if len(n_tst) > 0 else "N/A"
    
    print(f"{m:<22} | {ov_m:<12} | {nv_m:<12} | {ot_m:<13} | {nt_m:<13} | {os_k:<10} | {ns_k:<10}")

print("="*95)
