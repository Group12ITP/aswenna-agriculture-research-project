import pandas as pd
df = pd.read_csv('results/tables/test_refit_purge_comparison.csv')
naive_df = df[df['model'] == 'naive']
print(naive_df[['horizon', 'old_test_MASE', 'new_test_MASE']])
