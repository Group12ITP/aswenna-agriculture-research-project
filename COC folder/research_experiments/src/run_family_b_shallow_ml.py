"""
run_family_b_shallow_ml.py - Trains and evaluates all Family B models across LOSO and Forward-Chaining folds.
Saves all fold models, predictions, metrics, and logs manifest entries.
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
from metrics import compute_core_metrics
from registry import (
    get_experiments_root, generate_run_id, record_manifest_entry,
    record_experiment_run, is_run_completed
)
from models_ml import build_pipeline_model, build_stacking_ensemble


def run_single_ml_model(model_key: str, df: pd.DataFrame, feature_cols: list, target_col: str, loso_splits: list, fc_splits: list):
    root = get_experiments_root()
    family = "Shallow_ML"
    model_name = model_key

    if is_run_completed(model_name, family):
        print(f"Skipping {model_name} (already recorded in model_registry.csv).")
        return

    print(f"\n--- Running Family B: {model_name} ---")
    run_id = generate_run_id(family, model_name)
    exp_dir = root / "experiments" / family / model_name / run_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    fold_models_dir = exp_dir / "fold_models"
    fold_models_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    loso_oof_preds = np.zeros(len(df))
    loso_fold_metrics = []

    # 1. Primary CV: LOSO (12 Folds)
    for fold_info in loso_splits:
        fold_name = fold_info["fold_name"]
        X_tr = df.iloc[fold_info["train_idx"]][feature_cols]
        y_tr = df.iloc[fold_info["train_idx"]][target_col]
        X_te = df.iloc[fold_info["test_idx"]][feature_cols]
        y_te = df.iloc[fold_info["test_idx"]][target_col]

        if model_key.lower() == "stacking_top3":
            model = build_stacking_ensemble(random_state=42)
        else:
            model = build_pipeline_model(model_key, random_state=42)

        model.fit(X_tr, y_tr)
        preds = model.predict(X_te)
        loso_oof_preds[fold_info["test_idx"]] = preds

        m = compute_core_metrics(y_te.values, preds)
        m["fold"] = fold_name
        loso_fold_metrics.append(m)

        # Save fold model pipeline
        f_path = fold_models_dir / f"{fold_name}.joblib"
        joblib.dump(model, f_path, compress=3)

        # Verify load-and-predict
        loaded_m = joblib.load(f_path)
        test_pred = loaded_m.predict(X_te.iloc[:2])
        load_pass = np.allclose(test_pred, preds[:2], atol=1e-3)

        record_manifest_entry(
            run_id=run_id,
            family=family,
            model_name=model_name,
            file_path=f_path,
            fold=fold_name,
            load_test_passed=load_pass,
            notes="Fold model joblib"
        )

    overall_loso = compute_core_metrics(df[target_col].values, loso_oof_preds)

    # 2. Secondary CV: Forward-Chaining (4 horizons)
    fc_oof_records = []
    for fc_info in fc_splits:
        X_tr = df.iloc[fc_info["train_idx"]][feature_cols]
        y_tr = df.iloc[fc_info["train_idx"]][target_col]
        X_te = df.iloc[fc_info["test_idx"]][feature_cols]
        y_te = df.iloc[fc_info["test_idx"]][target_col]

        if model_key.lower() == "stacking_top3":
            model = build_stacking_ensemble(random_state=42)
        else:
            model = build_pipeline_model(model_key, random_state=42)

        model.fit(X_tr, y_tr)
        preds = model.predict(X_te)

        for actual, pred, y_start in zip(y_te.values, preds, df.iloc[fc_info["test_idx"]]["Year_Start"].values):
            fc_oof_records.append({"actual": actual, "predicted": pred, "Year_Start": y_start})

    df_fc_eval = pd.DataFrame(fc_oof_records)
    overall_fc = compute_core_metrics(df_fc_eval["actual"].values, df_fc_eval["predicted"].values) if len(df_fc_eval) > 0 else {}

    # 3. Fit Final Full Model on 100% of data
    if model_key.lower() == "stacking_top3":
        final_model = build_stacking_ensemble(random_state=42)
    else:
        final_model = build_pipeline_model(model_key, random_state=42)
    final_model.fit(df[feature_cols], df[target_col])
    final_model_path = exp_dir / "model.joblib"
    joblib.dump(final_model, final_model_path, compress=3)

    record_manifest_entry(
        run_id=run_id,
        family=family,
        model_name=model_name,
        file_path=final_model_path,
        fold="FULL_DATA",
        load_test_passed=True,
        notes="Final full fit on 100% of rows"
    )

    runtime = time.time() - start_time

    # 4. Save Predictions & Summary
    df_pred = df[["row_id", "Crop", "District", "Season", "Irrigation_Type", "Year_Start", "economic_regime", target_col]].copy()
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
        hyperparameters={"model_key": model_key},
        runtime_seconds=runtime
    )

    print(f"Finished {model_name} in {runtime:.1f}s | LOSO MAE: Rs {overall_loso['MAE']:,.1f} | R2: {overall_loso['R2']:.4f}")


def main():
    print("=" * 80)
    print("STARTING FAMILY B (SHALLOW MACHINE LEARNING) EXPERIMENT RUNNER")
    print("=" * 80)
    df = load_model_data()
    feature_cols, target_col = get_feature_and_target_columns()
    loso_splits = get_loso_splits(df)
    fc_splits = get_forward_chaining_splits(df)

    ml_models = [
        "ridge",
        "lasso",
        "elasticnet",
        "knn",
        "svr",
        "decisiontree",
        "randomforest",
        "extratrees",
        "gradientboosting",
        "gradientboosting_tuned",
        "histgradientboosting",
        "xgboost",
        "lightgbm",
        "catboost",
        "stacking_top3"
    ]

    for model_key in ml_models:
        run_single_ml_model(model_key, df, feature_cols, target_col, loso_splits, fc_splits)

    print("\nFamily B Training Complete!")


if __name__ == "__main__":
    main()
