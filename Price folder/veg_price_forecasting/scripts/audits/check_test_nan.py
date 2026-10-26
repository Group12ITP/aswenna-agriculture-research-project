import pandas as pd

df = pd.read_csv("experiments/runs/20261001_144816_prophet_h4/predictions_test.csv")
print("Total rows:", len(df))
print("Non-na y_true rows:", df["y_true"].notna().sum())
print("Null y_true rows:", df["y_true"].isna().sum())
print("Last 5 rows for Carrot:")
c = df[df["product_name"] == "Carrot"].tail(8)
print(c[["approx_date", "y_true", "y_pred"]])
