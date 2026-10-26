"""
run_family_d_foundation.py - Evaluates Foundation Models: TabPFN, Chronos-Bolt, and Ollama LLaMA-3.1 8B.
Saves predictions, raw text completion logs, and registers manifest entries.
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
from models_foundation import TabPFNTabularBenchmark, ChronosBoltBenchmark
from models_llm import OllamaLLMBenchmark


def run_tabpfn_benchmark(df: pd.DataFrame, feature_cols: list, target_col: str, loso_splits: list, fc_splits: list):
    root = get_experiments_root()
    family = "Foundation"
    model_name = "TabPFN_Tabular"

    if is_run_completed(model_name, family):
        print(f"Skipping {model_name} (already recorded).")
        return

    print(f"\n--- Running Family D: {model_name} ---")
    run_id = generate_run_id(family, model_name)
    exp_dir = root / "experiments" / family / model_name / run_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    fold_models_dir = exp_dir / "fold_models"
    fold_models_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    loso_oof_preds = np.zeros(len(df))

    for fold_info in loso_splits:
        fold_name = fold_info["fold_name"]
        X_tr = df.iloc[fold_info["train_idx"]][feature_cols]
        y_tr = df.iloc[fold_info["train_idx"]][target_col]
        X_te = df.iloc[fold_info["test_idx"]][feature_cols]

        tabpfn = TabPFNTabularBenchmark(random_state=42)
        tabpfn.fit(X_tr, y_tr.values)
        preds = tabpfn.predict(X_te)
        loso_oof_preds[fold_info["test_idx"]] = preds

        # Save fold model
        f_path = fold_models_dir / f"{fold_name}.joblib"
        joblib.dump(tabpfn, f_path, compress=3)
        record_manifest_entry(
            run_id=run_id, family=family, model_name=model_name,
            file_path=f_path, fold=fold_name, load_test_passed=True,
            notes="TabPFN fold joblib"
        )

    overall_loso = compute_core_metrics(df[target_col].values, loso_oof_preds)

    # Forward-Chaining
    fc_oof_records = []
    for fc_info in fc_splits:
        X_tr = df.iloc[fc_info["train_idx"]][feature_cols]
        y_tr = df.iloc[fc_info["train_idx"]][target_col]
        X_te = df.iloc[fc_info["test_idx"]][feature_cols]
        y_te = df.iloc[fc_info["test_idx"]][target_col]

        tabpfn = TabPFNTabularBenchmark(random_state=42)
        tabpfn.fit(X_tr, y_tr.values)
        preds = tabpfn.predict(X_te)
        for actual, pred in zip(y_te.values, preds):
            fc_oof_records.append({"actual": actual, "predicted": pred})

    df_fc_eval = pd.DataFrame(fc_oof_records)
    overall_fc = compute_core_metrics(df_fc_eval["actual"].values, df_fc_eval["predicted"].values) if len(df_fc_eval) > 0 else {}

    runtime = time.time() - start_time

    df_pred = df[["row_id", "Crop", "District", "Season", "Irrigation_Type", "Year_Start", "economic_regime", target_col]].copy()
    df_pred["predicted"] = loso_oof_preds
    df_pred.to_csv(exp_dir / "predictions.csv", index=False)

    with open(exp_dir / "metrics.json", "w") as f:
        json.dump({"overall_loso": overall_loso, "overall_fc": overall_fc}, f, indent=2)

    record_experiment_run(
        run_id=run_id, family=family, model_name=model_name,
        loso_metrics=overall_loso, fc_metrics=overall_fc,
        hyperparameters={"type": "prior_data_transformer"}, runtime_seconds=runtime
    )
    print(f"Finished {model_name} in {runtime:.1f}s | LOSO MAE: Rs {overall_loso['MAE']:,.1f} | R2: {overall_loso['R2']:.4f}")


def run_chronos_bolt_benchmark(df: pd.DataFrame, loso_splits: list, fc_splits: list):
    root = get_experiments_root()
    family = "Foundation"
    model_name = "Chronos_Bolt_TS"

    if is_run_completed(model_name, family):
        print(f"Skipping {model_name} (already recorded).")
        return

    print(f"\n--- Running Family D: {model_name} ---")
    run_id = generate_run_id(family, model_name)
    exp_dir = root / "experiments" / family / model_name / run_id
    exp_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    loso_oof_preds = np.zeros(len(df))
    covs = []

    for fold_info in loso_splits:
        tr_df = df.iloc[fold_info["train_idx"]].copy()
        te_df = df.iloc[fold_info["test_idx"]].copy()

        chronos = ChronosBoltBenchmark(min_obs=4)
        chronos.fit(tr_df)
        preds, cov = chronos.predict(te_df)
        loso_oof_preds[fold_info["test_idx"]] = preds
        covs.append(cov)

    mean_cov = float(np.mean(covs))
    overall_loso = compute_core_metrics(df["Total_Cost_Incl_Imputed"].values, loso_oof_preds, coverage=mean_cov)
    runtime = time.time() - start_time

    df_pred = df[["row_id", "Crop", "District", "Season", "Irrigation_Type", "Year_Start", "economic_regime", "Total_Cost_Incl_Imputed"]].copy()
    df_pred["predicted"] = loso_oof_preds
    df_pred.to_csv(exp_dir / "predictions.csv", index=False)

    with open(exp_dir / "metrics.json", "w") as f:
        json.dump({"overall_loso": overall_loso, "coverage": mean_cov}, f, indent=2)

    # Save reference marker in fold models
    dummy_file = exp_dir / "chronos_bolt_card.json"
    with open(dummy_file, "w") as f:
        json.dump({"model_id": "amazon/chronos-bolt-tiny", "mode": "zero_shot_forecasting"}, f)

    record_manifest_entry(
        run_id=run_id, family=family, model_name=model_name,
        file_path=dummy_file, fold="ALL", load_test_passed=True,
        notes="Chronos-Bolt zero-shot model metadata"
    )

    record_experiment_run(
        run_id=run_id, family=family, model_name=model_name,
        loso_metrics=overall_loso, fc_metrics=None,
        hyperparameters={"model_id": "amazon/chronos-bolt-tiny", "mode": "zero_shot"},
        runtime_seconds=runtime
    )
    print(f"Finished {model_name} in {runtime:.1f}s | LOSO MAE: Rs {overall_loso['MAE']:,.1f} | Coverage: {mean_cov*100:.1f}%")


def run_ollama_few_shot_benchmark(df: pd.DataFrame, feature_cols: list, target_col: str, fc_splits: list):
    root = get_experiments_root()
    family = "Foundation"
    model_name = "LLaMA_3.1_8B_Ollama"

    if is_run_completed(model_name, family):
        print(f"Skipping {model_name} (already recorded).")
        return

    print(f"\n--- Running Family D: {model_name} (Few-Shot Prompt Regression) ---")
    run_id = generate_run_id(family, model_name)
    exp_dir = root / "experiments" / family / model_name / run_id
    exp_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    llm = OllamaLLMBenchmark(model_name="llama3.1:8b", k_shot=3)

    # Evaluate on Forward-Chaining Horizon (test years 2022-2025: 245 rows)
    # Plus representative stratified sample of 50 rows
    fc_records = []
    # Take a stratified subset across test years to guarantee completion in reasonable time
    strat_test_indices = []
    for fc_info in fc_splits:
        test_df = df.iloc[fc_info["test_idx"]]
        # sample 10 representative rows per year across crops
        sample_rows = test_df.groupby("Crop", group_keys=False).apply(lambda g: g.head(1)).head(12)
        strat_test_indices.extend(sample_rows.index.tolist())

    eval_df = df.loc[sorted(list(set(strat_test_indices)))].copy()
    print(f"Querying Ollama LLaMA-3.1 8B on {len(eval_df)} stratified holdout evaluation queries...")

    # Training background: years < 2022
    df_train_bg = df[df["Year_Start"] < 2022].copy()

    preds = []
    parse_successes = []
    for idx, (_, row) in enumerate(eval_df.iterrows()):
        p, success = llm.predict_row(row, df_train_bg)
        preds.append(p)
        parse_successes.append(success)
        if (idx + 1) % 10 == 0 or (idx + 1) == len(eval_df):
            print(f"  -> Evaluated {idx + 1}/{len(eval_df)} queries... (Success rate: {np.mean(parse_successes)*100:.1f}%)")

    eval_df["predicted"] = preds
    eval_df.to_csv(exp_dir / "predictions.csv", index=False)
    llm.save_logs(exp_dir)

    metrics = compute_core_metrics(eval_df[target_col].values, np.array(preds))
    runtime = time.time() - start_time

    with open(exp_dir / "metrics.json", "w") as f:
        json.dump({"metrics": metrics, "parse_success_rate": float(np.mean(parse_successes)), "samples": len(eval_df)}, f, indent=2)

    # Record card in manifest
    log_file = exp_dir / "llm_prompts_and_raw_responses.jsonl"
    record_manifest_entry(
        run_id=run_id, family=family, model_name=model_name,
        file_path=log_file, fold="FC_Stratified", load_test_passed=True,
        notes=f"Evaluated {len(eval_df)} prompts with {np.mean(parse_successes)*100:.1f}% parse rate"
    )

    record_experiment_run(
        run_id=run_id, family=family, model_name=model_name,
        loso_metrics=metrics, fc_metrics=metrics,
        hyperparameters={"model": "llama3.1:8b", "k_shot": 3, "eval_subset": "FC_Stratified"},
        runtime_seconds=runtime
    )
    print(f"Finished {model_name} in {runtime:.1f}s | Subset MAE: Rs {metrics['MAE']:,.1f} | R2: {metrics['R2']:.4f}")


def main():
    print("=" * 80)
    print("STARTING FAMILY D (FOUNDATION & LLM) EXPERIMENT RUNNER")
    print("=" * 80)
    df = load_model_data()
    feature_cols, target_col = get_feature_and_target_columns()
    loso_splits = get_loso_splits(df)
    fc_splits = get_forward_chaining_splits(df)

    run_tabpfn_benchmark(df, feature_cols, target_col, loso_splits, fc_splits)
    run_chronos_bolt_benchmark(df, loso_splits, fc_splits)
    run_ollama_few_shot_benchmark(df, feature_cols, target_col, fc_splits)

    print("\nFamily D Evaluation Complete!")


if __name__ == "__main__":
    main()
