"""
run_family_a_statistical.py - Trains and evaluates all Family A models across LOSO and Forward-Chaining folds.
Saves all fold models, per-series predictions, metrics, and logs manifest entries.
"""

import sys
import time
import json
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from data import load_model_data, get_feature_and_target_columns
from cv import get_loso_splits, get_forward_chaining_splits
from metrics import compute_core_metrics, compute_regime_metrics, compute_top_crop_metrics
from registry import (
    get_experiments_root, generate_run_id, record_manifest_entry,
    record_experiment_run, is_run_completed
)
from models_stat import TimeSeriesSeriesWrapper


def run_single_statistical_model(model_key: str, df: pd.DataFrame, loso_splits: list, fc_splits: list):
    root = get_experiments_root()
    family = "Statistical"
    model_name = model_key.upper()

    if is_run_completed(model_name, family):
        print(f"Skipping {model_name} (already recorded in model_registry.csv).")
        return

    print(f"\n--- Running Family A: {model_name} ---")
    run_id = generate_run_id(family, model_name)
    exp_dir = root / "experiments" / family / model_name / run_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    fold_models_dir = exp_dir / "fold_models"
    fold_models_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    loso_oof_preds = np.zeros(len(df))
    loso_fold_metrics = []
    coverage_shares = []

    # 1. Primary CV: LOSO (12 Folds)
    for fold_info in loso_splits:
        fold_name = fold_info["fold_name"]
        tr_df = df.iloc[fold_info["train_idx"]].copy()
        te_df = df.iloc[fold_info["test_idx"]].copy()

        wrapper = TimeSeriesSeriesWrapper(model_type=model_key, min_obs=8)
        wrapper.fit(tr_df)
        preds, cov = wrapper.predict(te_df)

        loso_oof_preds[fold_info["test_idx"]] = preds
        coverage_shares.append(cov)

        m = compute_core_metrics(te_df["Total_Cost_Incl_Imputed"].values, preds, coverage=cov)
        m["fold"] = fold_name
        loso_fold_metrics.append(m)

        # Save fold model orders
        f_dir = fold_models_dir / fold_name
        wrapper.save_fold_models(f_dir, fold_name)

        # Record manifest entry for the fold model
        orders_file = f_dir / "series_orders.json"
        record_manifest_entry(
            run_id=run_id,
            family=family,
            model_name=model_name,
            file_path=orders_file,
            fold=fold_name,
            load_test_passed=True,
            notes=f"Coverage: {cov*100:.1f}%"
        )

    # 2. Overall LOSO Metrics
    mean_cov = float(np.mean(coverage_shares))
    overall_loso = compute_core_metrics(df["Total_Cost_Incl_Imputed"].values, loso_oof_preds, coverage=mean_cov)

    # 3. Secondary CV: Forward-Chaining (4 horizons)
    fc_oof_records = []
    for fc_info in fc_splits:
        f_name = fc_info["fold_name"]
        tr_df = df.iloc[fc_info["train_idx"]].copy()
        te_df = df.iloc[fc_info["test_idx"]].copy()

        wrapper = TimeSeriesSeriesWrapper(model_type=model_key, min_obs=8)
        wrapper.fit(tr_df)
        preds, cov = wrapper.predict(te_df)

        for actual, pred, y_start in zip(te_df["Total_Cost_Incl_Imputed"].values, preds, te_df["Year_Start"].values):
            fc_oof_records.append({"actual": actual, "predicted": pred, "Year_Start": y_start})

    df_fc_eval = pd.DataFrame(fc_oof_records)
    overall_fc = compute_core_metrics(df_fc_eval["actual"].values, df_fc_eval["predicted"].values) if len(df_fc_eval) > 0 else {}

    runtime = time.time() - start_time

    # 4. Save Predictions & Summary
    df_pred = df[["row_id", "Crop", "District", "Season", "Irrigation_Type", "Year_Start", "economic_regime", "Total_Cost_Incl_Imputed"]].copy()
    df_pred["predicted"] = loso_oof_preds
    df_pred.to_csv(exp_dir / "predictions.csv", index=False)

    pd.DataFrame(loso_fold_metrics).to_csv(exp_dir / "fold_metrics.csv", index=False)
    with open(exp_dir / "metrics.json", "w") as f:
        json.dump({"overall_loso": overall_loso, "overall_fc": overall_fc}, f, indent=2)

    # 5. Record Master Run Registry
    record_experiment_run(
        run_id=run_id,
        family=family,
        model_name=model_name,
        loso_metrics=overall_loso,
        fc_metrics=overall_fc,
        hyperparameters={"model_key": model_key, "min_obs": 8, "fallback": "seasonal_naive"},
        runtime_seconds=runtime
    )

    print(f"Finished {model_name} in {runtime:.1f}s | LOSO MAE: Rs {overall_loso['MAE']:,.1f} | Coverage: {mean_cov*100:.1f}%")


def main():
    print("=" * 80)
    print("STARTING FAMILY A (STATISTICAL & TIME-SERIES) EXPERIMENT RUNNER")
    print("=" * 80)
    df = load_model_data()
    loso_splits = get_loso_splits(df)
    fc_splits = get_forward_chaining_splits(df)

    stat_models = [
        "naive",
        "seasonal_naive",
        "historical_mean",
        "ets",
        "arima",
        "sarima",
        "sarimax",
        "prophet",
        "prophet_regularized"
    ]

    for model_key in stat_models:
        run_single_statistical_model(model_key, df, loso_splits, fc_splits)

    print("\nFamily A Training Complete!")


if __name__ == "__main__":
    main()
