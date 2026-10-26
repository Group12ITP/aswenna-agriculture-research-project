from pathlib import Path
import pandas as pd

for p in sorted(Path("experiments/runs").glob("*_prophet_h4")):
    pred_file = p / "predictions_test.csv"
    if pred_file.exists():
        df = pd.read_csv(pred_file)
        print(p.name, len(df), "vegs:", len(df["product_name"].unique()))
