import pandas as pd
df = pd.read_csv('experiments/leaderboard.csv')
sub = df[(df['model']=='auto_arima') & (df['horizon']==4) & (df['split']=='test')]
print(sub[['model', 'Coverage_80', 'Width_80_LKR', 'Width_80_Pct', 'Coverage_95', 'Width_95_LKR', 'Width_95_Pct']].to_dict(orient='records'))
