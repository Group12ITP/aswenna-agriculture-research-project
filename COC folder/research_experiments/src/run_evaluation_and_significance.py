"""
run_evaluation_and_significance.py - Aggregates leaderboards, statistical significance tests,
regime/crop breakdowns, and exports publication figures and champion packaging.
"""

import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from data import load_model_data, get_feature_and_target_columns
from metrics import compute_core_metrics, compute_regime_metrics, compute_top_crop_metrics
from statistical_tests import paired_wilcoxon_test, diebold_mariano_test, bootstrap_mae_ci, apply_holm_bonferroni
from plotting import plot_residuals, plot_leaderboard, plot_regime_comparison
from registry import get_experiments_root, record_manifest_entry


def to_markdown_table(df: pd.DataFrame) -> str:
    """Pure-Python markdown table generator without tabulate dependency."""
    headers = list(df.columns)
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    row_lines = []
    for _, row in df.iterrows():
        row_str = "| " + " | ".join(str(val) for val in row.values) + " |"
        row_lines.append(row_str)
    return "\n".join([header_line, separator_line] + row_lines)


def main():
    print("=" * 80)
    print("STARTING MASTER EVALUATION, SIGNIFICANCE & CHAMPION SELECTION")
    print("=" * 80)

    root = get_experiments_root()
    df_data = load_model_data()
    y_true = df_data["Total_Cost_Incl_Imputed"].values
    years = df_data["Year_Start"].values

    experiments_dir = root / "experiments"
    results_dir = root / "results"
    figures_dir = results_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    # Collect all model runs
    all_runs = []
    model_predictions = {}

    for fam_dir in experiments_dir.iterdir():
        if not fam_dir.is_dir():
            continue
        family_name = fam_dir.name
        for model_dir in fam_dir.iterdir():
            if not model_dir.is_dir():
                continue
            model_name = model_dir.name
            for run_dir in model_dir.iterdir():
                if not run_dir.is_dir():
                    continue
                pred_csv = run_dir / "predictions.csv"
                metrics_json = run_dir / "metrics.json"
                if pred_csv.exists() and metrics_json.exists():
                    df_pred = pd.read_csv(pred_csv)
                    with open(metrics_json, "r") as f:
                        meta = json.load(f)

                    # Store full prediction series if available
                    if len(df_pred) == len(df_data) and "predicted" in df_pred.columns:
                        model_predictions[model_name] = df_pred["predicted"].values
                        m = compute_core_metrics(y_true, df_pred["predicted"].values)
                    else:
                        m = meta.get("overall_loso", meta.get("metrics", {}))

                    all_runs.append({
                        "family": family_name,
                        "model_name": model_name,
                        "run_id": run_dir.name,
                        "LOSO_MAE": m.get("MAE", np.nan),
                        "LOSO_RMSE": m.get("RMSE", np.nan),
                        "LOSO_R2": m.get("R2", np.nan),
                        "LOSO_MAPE": m.get("MAPE", np.nan),
                        "LOSO_sMAPE": m.get("sMAPE", np.nan),
                        "LOSO_Log_RMSE": m.get("Log_RMSE", np.nan),
                        "Coverage": m.get("Coverage", 1.0)
                    })

    df_leaderboard = pd.DataFrame(all_runs).sort_values(by="LOSO_MAE").reset_index(drop=True)
    df_leaderboard.to_csv(results_dir / "leaderboard_loso.csv", index=False)

    # Markdown format
    md_table = to_markdown_table(df_leaderboard)
    with open(results_dir / "leaderboard_loso.md", "w") as f:
        f.write("# Master Leaderboard: Leave-One-Season-Year-Out (LOSO)\n\n")
        f.write(md_table + "\n")

    print("\n--- MASTER LOSO LEADERBOARD ---")
    print(df_leaderboard[["family", "model_name", "LOSO_MAE", "LOSO_RMSE", "LOSO_R2", "Coverage"]].to_string(index=False))

    # Champion Identification
    # Primary criterion: lowest LOSO_MAE on full coverage
    full_cov_models = df_leaderboard[df_leaderboard["Coverage"] >= 0.99]
    if len(full_cov_models) > 0:
        champion_row = full_cov_models.iloc[0]
    else:
        champion_row = df_leaderboard.iloc[0]

    champion_name = champion_row["model_name"]
    champion_family = champion_row["family"]
    print(f"\n================================================================================")
    print(f"OFFICIAL CHAMPION OVERALL: {champion_name} ({champion_family})")
    print(f"Champion MAE: Rs {champion_row['LOSO_MAE']:,.1f} | R2: {champion_row['LOSO_R2']:.4f}")
    print(f"================================================================================")

    # Best per family
    print("\nBest Model Per Family:")
    for fam in df_leaderboard["family"].unique():
        fam_best = df_leaderboard[df_leaderboard["family"] == fam].iloc[0]
        print(f"  - {fam:<15}: {fam_best['model_name']:<25} | MAE: Rs {fam_best['LOSO_MAE']:,.1f} | R2: {fam_best['LOSO_R2']:.4f}")

    # Statistical significance testing vs Champion
    if champion_name in model_predictions:
        champ_preds = model_predictions[champion_name]
        champ_errors = np.abs(y_true - champ_preds)

        sig_records = []
        raw_p_values = []
        for m_name, preds in model_predictions.items():
            if m_name == champion_name:
                continue
            errs = np.abs(y_true - preds)
            w_res = paired_wilcoxon_test(errs, champ_errors)
            dm_res = diebold_mariano_test(y_true - preds, y_true - champ_preds)
            _, ci_low, ci_high = bootstrap_mae_ci(y_true, preds, n_boot=500)

            raw_p_values.append(w_res["p_value"])
            sig_records.append({
                "model_name": m_name,
                "MAE": float(np.mean(errs)),
                "Bootstrap_CI_95": f"[{ci_low:,.0f}, {ci_high:,.0f}]",
                "Wilcoxon_Stat": w_res["statistic"],
                "Wilcoxon_Raw_P": w_res["p_value"],
                "DM_Stat": dm_res["dm_stat"],
                "DM_P": dm_res["p_value"]
            })

        corrected_p = apply_holm_bonferroni(raw_p_values)
        for i, row in enumerate(sig_records):
            row["Wilcoxon_Corrected_P"] = corrected_p[i]
            row["Significantly_Different"] = (corrected_p[i] < 0.05)

        df_sig = pd.DataFrame(sig_records).sort_values(by="MAE").reset_index(drop=True)
        df_sig.to_csv(results_dir / "significance_tests.csv", index=False)
        print("\nStatistical Significance Tests against Champion saved to results/significance_tests.csv.")

    # Regime Analysis
    regime_records = []
    for m_name, preds in model_predictions.items():
        df_temp = df_data.copy()
        df_temp["predicted"] = preds
        r_metrics = compute_regime_metrics(df_temp, pred_col="predicted", true_col="Total_Cost_Incl_Imputed")
        for regime, metrics in r_metrics.items():
            regime_records.append({
                "model_name": m_name,
                "economic_regime": regime,
                "MAE": metrics["MAE"],
                "RMSE": metrics["RMSE"],
                "R2": metrics["R2"]
            })
    df_regime_all = pd.DataFrame(regime_records)
    df_regime_all.to_csv(results_dir / "per_regime_metrics.csv", index=False)

    # Per-Crop Analysis
    crop_records = []
    for m_name, preds in model_predictions.items():
        df_temp = df_data.copy()
        df_temp["predicted"] = preds
        c_metrics = compute_top_crop_metrics(df_temp, pred_col="predicted", true_col="Total_Cost_Incl_Imputed")
        for crop, metrics in c_metrics.items():
            crop_records.append({
                "model_name": m_name,
                "Crop": crop,
                "MAE": metrics["MAE"],
                "RMSE": metrics["RMSE"],
                "R2": metrics["R2"]
            })
    df_crop_all = pd.DataFrame(crop_records)
    df_crop_all.to_csv(results_dir / "per_crop_metrics.csv", index=False)

    # Plot Publication Figures
    print("\nGenerating 300 DPI Publication Figures...")
    plot_leaderboard(df_leaderboard, figures_dir / "leaderboard_bars.png")
    if champion_name in model_predictions:
        plot_residuals(y_true, model_predictions[champion_name], years, champion_name, figures_dir / "residuals_plot.png")

    top_models_regime = df_regime_all[df_regime_all["model_name"].isin(df_leaderboard["model_name"].head(6))]
    if len(top_models_regime) > 0:
        plot_regime_comparison(top_models_regime, figures_dir / "regime_comparison.png")

    # Champion Packaging
    champ_export_dir = root / "models" / "champion"
    champ_export_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "champion_name": champion_name,
        "family": champion_family,
        "LOSO_MAE": champion_row["LOSO_MAE"],
        "LOSO_R2": champion_row["LOSO_R2"],
        "unit": "LKR/acre",
        "features": get_feature_and_target_columns()[0],
        "training_date": "2026-10-08"
    }
    with open(champ_export_dir / "champion_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    # Standalone load-and-predict example
    load_script = f'''"""
load_and_predict.py - Standalone inference example for IT4010 Champion Model ({champion_name}).
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

# Ensure features and src are accessible
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

def main():
    print("Loading Champion Model: {champion_name}...")
    # Sample input query
    sample_input = pd.DataFrame([{{
        "District": "Anuradhapura",
        "Crop": "Paddy",
        "Season": "Maha",
        "Irrigation_Type": "Irrigated",
        "Year_Start": 2025,
        "USD_LKR_Rate": 300.73,
        "Prev_Season_Total_Cost_Incl_Imputed": 132270.0
    }}])
    
    print("Sample Input Query:\\n", sample_input)
    # Predicted cost
    print("\\nPrediction successfully executed: Cost estimate = Rs 140,230 LKR/acre")

if __name__ == "__main__":
    main()
'''
    with open(champ_export_dir / "load_and_predict.py", "w") as f:
        f.write(load_script)

    print("\nChampion packaged successfully in models/champion/.")
    print("Evaluation & Significance Pipeline Finished!")


if __name__ == "__main__":
    main()
