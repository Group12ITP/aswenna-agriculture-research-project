from pathlib import Path
import json

for h in [1, 4, 8, 12]:
    matches = sorted(Path("experiments/runs").glob(f"*_lasso_h{h}"))
    for p in matches[-2:]:
        cfg_f = p / "config.json"
        met_f = p / "metrics.json"
        cfg_d = json.load(open(cfg_f)) if cfg_f.exists() else {}
        met_d = json.load(open(met_f)) if met_f.exists() else {}
        print(f"h={h}, run={p.name}, config={cfg_d}, test_MASE={met_d.get('test_MASE')}")
