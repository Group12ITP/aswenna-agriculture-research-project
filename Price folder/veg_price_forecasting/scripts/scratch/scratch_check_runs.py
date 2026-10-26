from pathlib import Path
import pandas as pd
for m in ["naive", "lasso", "auto_arima"]:
    matches = sorted(Path("experiments/runs").glob(f"*_{m}_h4"))
    for p in matches:
        df = pd.read_csv(p / "predictions_test.csv")
        print(m, p.name, len(df))
