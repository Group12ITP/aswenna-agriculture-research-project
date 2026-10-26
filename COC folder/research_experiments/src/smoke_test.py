"""
smoke_test.py - Automated fast verification suite (1 fold / tiny epochs) across all 4 families.
"""

import sys
from pathlib import Path
import time
import numpy as np
import pandas as pd
import torch

# Ensure src is on sys.path
src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from data import load_model_data, get_feature_and_target_columns
from features import build_leak_free_preprocessor
from cv import get_loso_splits, get_forward_chaining_splits
from metrics import compute_core_metrics
from registry import record_manifest_entry, compute_sha256
from models_stat import TimeSeriesSeriesWrapper
from models_ml import build_pipeline_model
from models_dl import TabularMLP, TabularDataset
from models_foundation import TabPFNTabularBenchmark
from models_llm import extract_numeric_cost


def run_smoke_test():
    print("=" * 80)
    print("STARTING IT4010 RESEARCH SUITE SMOKE TEST (1 FOLD / ALL 4 FAMILIES)")
    print("=" * 80)

    # 1. Ingestion check
    print("\n[1/8] Verifying Data Ingestion & Indexing...")
    df = load_model_data()
    feature_cols, target_col = get_feature_and_target_columns()
    print(f"  -> Successfully loaded {len(df)} rows across {df['Crop'].nunique()} crops and {df['District'].nunique()} districts.")
    print(f"  -> Series count: {df['series_key'].nunique()} distinct Crop x District x Irrigation series.")
    assert len(df) == 641, f"Expected 641 rows, got {len(df)}"

    # 2. CV check
    print("\n[2/8] Verifying Cross-Validation Splits...")
    loso_splits = get_loso_splits(df)
    fc_splits = get_forward_chaining_splits(df)
    print(f"  -> Generated {len(loso_splits)} LOSO folds and {len(fc_splits)} Forward-Chaining horizons.")
    assert len(loso_splits) == 12, f"Expected 12 LOSO folds, got {len(loso_splits)}"
    assert len(fc_splits) == 4, f"Expected 4 FC horizons, got {len(fc_splits)}"

    test_fold = loso_splits[0]  # Held out year 2014
    train_df = df.iloc[test_fold["train_idx"]].copy()
    test_df = df.iloc[test_fold["test_idx"]].copy()
    print(f"  -> Test fold '{test_fold['fold_name']}': {len(train_df)} train rows, {len(test_df)} test rows.")

    # 3. Features check
    print("\n[3/8] Verifying Leak-Free Preprocessor...")
    prep = build_leak_free_preprocessor(random_state=42)
    X_tr = train_df[feature_cols]
    y_tr = train_df[target_col]
    prep.fit(X_tr, np.log1p(y_tr))
    X_tr_trans = prep.transform(X_tr)
    X_te_trans = prep.transform(test_df[feature_cols])
    print(f"  -> Transformed feature shape: train {X_tr_trans.shape}, test {X_te_trans.shape}")

    # 4. Family A (Statistical / Time-Series) smoke test
    print("\n[4/8] Smoke Testing Family A (Statistical & Time-Series)...")
    ts_wrapper = TimeSeriesSeriesWrapper(model_type="arima", min_obs=8)
    ts_wrapper.fit(train_df)
    stat_preds, coverage = ts_wrapper.predict(test_df)
    stat_metrics = compute_core_metrics(test_df[target_col].values, stat_preds, coverage=coverage)
    print(f"  -> ARIMA Smoke Test: MAE = Rs {stat_metrics['MAE']:,.1f}, Coverage = {coverage*100:.1f}%")

    # 5. Family B (Shallow ML) smoke test
    print("\n[5/8] Smoke Testing Family B (Shallow ML)...")
    ml_pipe = build_pipeline_model("gradientboosting", random_state=42)
    ml_pipe.fit(X_tr, y_tr)
    ml_preds = ml_pipe.predict(test_df[feature_cols])
    ml_metrics = compute_core_metrics(test_df[target_col].values, ml_preds)
    print(f"  -> GradientBoosting Smoke Test: MAE = Rs {ml_metrics['MAE']:,.1f}, R2 = {ml_metrics['R2']:.4f}")

    # 6. Family C (Deep Learning) smoke test
    print("\n[6/8] Smoke Testing Family C (Deep Learning PyTorch MLP)...")
    cat_cards = [25, 23, 2, 3]
    emb_dims = [8, 8, 2, 2]
    mlp = TabularMLP(cat_cards, emb_dims, num_cont=3, hidden_dims=[32, 16])
    dummy_cat = torch.zeros((5, 4), dtype=torch.long)
    dummy_cont = torch.randn((5, 3), dtype=torch.float32)
    out = mlp(dummy_cat, dummy_cont)
    print(f"  -> PyTorch MLP forward pass output shape: {out.shape} (Success)")

    # 7. Family D (Foundation Models) smoke test
    print("\n[7/8] Smoke Testing Family D (Foundation Models)...")
    tabpfn = TabPFNTabularBenchmark(random_state=42)
    tabpfn.fit(X_tr, y_tr.values)
    tabpfn_preds = tabpfn.predict(test_df[feature_cols])
    tabpfn_metrics = compute_core_metrics(test_df[target_col].values, tabpfn_preds)
    print(f"  -> TabPFN Benchmark Smoke Test: MAE = Rs {tabpfn_metrics['MAE']:,.1f}")

    # Numeric Regex Parser check for LLMs
    sample_text = "The predicted cultivation cost for this farm is approximately Rs. 145,250 per acre."
    parsed = extract_numeric_cost(sample_text)
    assert parsed == 145250.0, f"Expected 145250.0, got {parsed}"
    print(f"  -> LLM Strict Numeric Regex Parser: Successfully parsed '{parsed}' from sample text.")

    # 8. Manifest & Checksum recording check
    print("\n[8/8] Verifying Registry & Manifest System...")
    root = Path(__file__).resolve().parent.parent
    dummy_model_file = root / "models" / "smoke_test_marker.txt"
    with open(dummy_model_file, "w") as f:
        f.write("SMOKE_TEST_PASSED_2026")

    record_manifest_entry(
        run_id="smoke_test_run",
        family="Test",
        model_name="SmokeTestMarker",
        file_path=dummy_model_file,
        fold="LOSO_2014",
        load_test_passed=True,
        notes="Automated smoke test marker"
    )
    manifest_file = root / "models" / "model_manifest.csv"
    assert manifest_file.exists(), "Manifest file not created"
    print(f"  -> Manifest successfully logged at {manifest_file.relative_to(root)} with SHA-256: {compute_sha256(dummy_model_file)}")

    print("\n" + "=" * 80)
    print("ALL SMOKE TESTS PASSED CLEANLY! PIPELINE READY FOR FULL RUNS.")
    print("=" * 80)


if __name__ == "__main__":
    run_smoke_test()
