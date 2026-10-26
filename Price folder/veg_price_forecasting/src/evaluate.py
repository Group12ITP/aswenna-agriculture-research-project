import os
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from .utils import load_config, get_logger
from .metrics import diebold_mariano_test

logger = get_logger("src.evaluate")

# Set aesthetic publication styles
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight"
})

def generate_thesis_figures(exp_dir, results_dir, cfg=None):
    """Generate high-resolution PNG and SVG publication figures."""
    exp_path = Path(exp_dir)
    res_path = Path(results_dir)
    fig_path = res_path / "figures"
    fig_path.mkdir(parents=True, exist_ok=True)
    
    df_lead = pd.read_csv(exp_path / "leaderboard.csv")
    df_by_veg = pd.read_csv(exp_path / "leaderboard_by_vegetable.csv")
    
    # 1. Metric Heatmap: Model x Vegetable sMAPE at h=4 (top 15 models for clarity)
    h4_by_veg = df_by_veg[df_by_veg["horizon"] == 4]
    top_models_h4 = h4_by_veg.groupby("model")["test_MASE"].median().sort_values().head(16).index
    pivot_smape = h4_by_veg[h4_by_veg["model"].isin(top_models_h4)].pivot(
        index="model", columns="vegetable", values="test_sMAPE"
    )
    if not pivot_smape.empty:
        plt.figure(figsize=(18, 8))
        sns.heatmap(pivot_smape, cmap="YlGnBu", annot=True, fmt=".1f", cbar_kws={'label': 'Test sMAPE (%)'})
        plt.title("Cross-Vegetable Forecast Accuracy Heatmap (Primary Horizon h = 4 Weeks)")
        plt.ylabel("Model Architecture")
        plt.xlabel("Vegetable Variety")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(fig_path / "heatmap_smape_h4.png")
        plt.savefig(fig_path / "heatmap_smape_h4.svg")
        plt.close()
        
    # 2. Multi-Horizon Degradation Curve (MASE vs Horizon)
    test_df = df_lead[df_lead["split"] == "test"]
    
    plt.figure(figsize=(10, 6))
    top_models = test_df.groupby("model")["MASE"].median().sort_values().head(8).index
    for m in top_models:
        sub = test_df[test_df["model"] == m].sort_values("horizon")
        plt.plot(sub["horizon"], sub["MASE"], marker="o", linewidth=2, label=m)
    plt.title("Forecast Horizon Degradation Curve (Test Set MASE)")
    plt.xlabel("Forecast Horizon h (Weeks Ahead)")
    plt.ylabel("Test Median MASE")
    plt.xticks([1, 4, 8, 12])
    plt.legend(title="Model", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(fig_path / "horizon_degradation_mase.png")
    plt.savefig(fig_path / "horizon_degradation_mase.svg")
    plt.close()
    
    # 3. Prediction Interval Calibration Plot (Empirical vs Nominal Coverage)
    plt.figure(figsize=(12, 6))
    h4_test = test_df[test_df["horizon"] == 4].dropna(subset=["Coverage_80"]).sort_values("MASE")
    if not h4_test.empty:
        x = np.arange(len(h4_test))
        width = 0.35
        plt.bar(x - width/2, h4_test["Coverage_80"], width, label="80% Nominal Target", color="#4C72B0", alpha=0.85)
        plt.bar(x + width/2, h4_test["Coverage_95"], width, label="95% Nominal Target", color="#55A868", alpha=0.85)
        plt.axhline(80, color="#4C72B0", linestyle="--", linewidth=1.5)
        plt.axhline(95, color="#55A868", linestyle="--", linewidth=1.5)
        plt.xticks(x, h4_test["model"], rotation=45, ha="right")
        plt.ylabel("Empirical Coverage Rate (%)")
        plt.title("Empirical Scale-Aware Prediction Interval Coverage at Horizon h=4")
        plt.legend()
        plt.ylim(0, 105)
        plt.tight_layout()
        plt.savefig(fig_path / "interval_coverage_h4.png")
        plt.savefig(fig_path / "interval_coverage_h4.svg")
        plt.close()
        
    logger.info(f"Generated publication figures in {fig_path}")

def generate_thesis_tables(exp_dir, results_dir):
    """Generate publication CSV and LaTeX tables."""
    exp_path = Path(exp_dir)
    res_path = Path(results_dir)
    tbl_path = res_path / "tables"
    tbl_path.mkdir(parents=True, exist_ok=True)
    
    df_lead = pd.read_csv(exp_path / "leaderboard.csv")
    
    # Table 1: Main Model Comparison at Primary Horizon h=4
    h4_df = df_lead[df_lead["horizon"] == 4].copy()
    val_h4 = h4_df[h4_df["split"] == "validation"].set_index("model")
    test_h4 = h4_df[h4_df["split"] == "test"].set_index("model")
    
    width_col = "Width_80_LKR" if "Width_80_LKR" in test_h4.columns else "Width_80"
    width_pct_col = "Width_80_Pct" if "Width_80_Pct" in test_h4.columns else None
    
    table1 = pd.DataFrame({
        "Val MASE": val_h4["MASE"],
        "Val sMAPE (%)": val_h4["sMAPE"],
        "Test MASE": test_h4["MASE"],
        "Test sMAPE (%)": test_h4["sMAPE"],
        "Test RMSE (Rs)": test_h4["RMSE"],
        "Test R2": test_h4["R2"],
        "Test DA (%)": test_h4["Directional_Accuracy"] if "Directional_Accuracy" in test_h4.columns else np.nan,
        "Test Cov 80%": test_h4["Coverage_80"] if "Coverage_80" in test_h4.columns else np.nan,
        "Test Width 80% (Rs)": test_h4[width_col] if width_col in test_h4.columns else np.nan,
    })
    if width_pct_col and width_pct_col in test_h4.columns:
        table1["Test Width 80% (%)"] = test_h4[width_pct_col]
    table1 = table1.sort_values("Val MASE")
    
    table1.to_csv(tbl_path / "table1_main_model_comparison_h4.csv")
    with open(tbl_path / "table1_main_model_comparison_h4.tex", "w", encoding="utf-8") as f:
        f.write(table1.to_latex(float_format="%.2f", caption="Main Model Comparison at Primary Horizon h=4 Weeks"))
        
    # Table 2: Multi-Horizon Progression Table
    test_pivot = df_lead[df_lead["split"] == "test"].pivot(
        index="model", columns="horizon", values="sMAPE"
    )
    test_pivot.columns = [f"h={c} (sMAPE %)" for c in test_pivot.columns]
    test_pivot.to_csv(tbl_path / "table2_multi_horizon_smape.csv")
    with open(tbl_path / "table2_multi_horizon_smape.tex", "w", encoding="utf-8") as f:
        f.write(test_pivot.to_latex(float_format="%.2f", caption="Multi-Horizon Forecast Accuracy Across Horizons (1, 4, 8, 12)"))
        
    logger.info(f"Generated publication LaTeX and CSV tables in {tbl_path}")
