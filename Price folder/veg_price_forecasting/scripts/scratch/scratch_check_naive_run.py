import pandas as pd
from pathlib import Path
for p in sorted(Path("experiments/runs").glob("*_naive_h4")):
    df = pd.read_csv(p / "predictions_test.csv")
    print(p.name, len(df))
    print("Columns:", df.columns.tolist())
    print("Sample:", df.head(3))
    break
