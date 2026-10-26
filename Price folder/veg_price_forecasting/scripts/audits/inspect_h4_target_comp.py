import pandas as pd
import numpy as np

# Load target formulation comparison
t_comp = pd.read_csv("results/tables/target_formulation_comparison.csv")
print("Target formulation comparison at h=4:")
print(t_comp[t_comp["horizon"] == 4][["model", "val_MASE_level", "val_MASE_ratio", "chosen_target_mode", "val_MASE_gain_pct", "test_skill_level", "test_skill_ratio"]].to_string())
