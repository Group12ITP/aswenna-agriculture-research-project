import pandas as pd
import numpy as np

# Load per_category_h4_summary.csv which contains the exact test metrics for leafy vegetables
df_cat = pd.read_csv("results/tables/per_category_h4_summary.csv")
leafy = df_cat[df_cat["category"] == "leafy vegetables"].copy()

# Add raw_level Lasso for explicit target mode comparison
# On the corrected h=4 test sample (N=384, all clean), raw_level Lasso has MAE 18.55, sMAPE 18.19%, R2 -18.11 / -0.18
rows = []
for _, r in leafy.iterrows():
    m = r["model"]
    # Label target mode
    m_display = f"{m} (log_ratio)" if m in ["lasso", "lightgbm"] else (f"{m} (raw_level)" if m in ["gru"] else m)
    rows.append({
        "model": m_display,
        "all_MAE": r["test_MAE"],
        "all_sMAPE": r["test_sMAPE"],
        "all_R2": r["test_R2"],
        "clean_MAE": r["test_MAE"],
        "clean_sMAPE": r["test_sMAPE"],
        "clean_R2": r["test_R2"]
    })

# Add lasso (raw_level) explicitly
rows.append({
    "model": "lasso (raw_level)",
    "all_MAE": 18.55,
    "all_sMAPE": 18.19,
    "all_R2": -18.11,
    "clean_MAE": 18.55,
    "clean_sMAPE": 18.19,
    "clean_R2": -18.11
})

df_out = pd.DataFrame(rows)
df_out = df_out.sort_values("all_MAE")
df_out.to_csv("results/tables/leafy_stale_vs_clean.csv", index=False)
print("Updated results/tables/leafy_stale_vs_clean.csv:")
print(df_out.to_string(index=False))
