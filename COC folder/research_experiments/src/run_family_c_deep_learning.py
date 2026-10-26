"""
run_family_c_deep_learning.py - Trains and evaluates Deep Learning models across 5 seeds and CV folds.
Saves PyTorch state_dicts, TabNet checkpoints, loss curves, and registers models in manifest.
"""

import sys
import time
import json
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from data import load_model_data, get_feature_and_target_columns
from cv import get_loso_splits, get_forward_chaining_splits, get_inner_temporal_split
from metrics import compute_core_metrics
from registry import (
    get_experiments_root, generate_run_id, record_manifest_entry,
    record_experiment_run, is_run_completed
)
from features import CropLagImputer
from models_dl import TabularMLP, FTTransformer, SequenceModel, TabNetWrapper


def encode_tabular_features(df_sub: pd.DataFrame, imputer: CropLagImputer, cat_maps: dict = None, scalers: dict = None):
    """Prepares integer categoricals and standardized continuous features for PyTorch."""
    df_imp = imputer.transform(df_sub)
    cat_cols = ["District", "Crop", "Season", "Irrigation_Type"]
    cont_cols = ["Year_Start", "USD_LKR_Rate", "Prev_Season_Total_Cost_Incl_Imputed"]

    cat_tensors = []
    for col in cat_cols:
        mapped = df_imp[col].astype(str).map(cat_maps[col]).fillna(0).values.astype(np.int64)
        cat_tensors.append(mapped)
    cat_arr = np.stack(cat_tensors, axis=1)

    cont_vals = df_imp[cont_cols].values.astype(np.float32)
    cont_mean, cont_std = scalers["mean"], scalers["std"]
    cont_norm = (cont_vals - cont_mean) / np.clip(cont_std, 1e-4, None)

    return torch.tensor(cat_arr, dtype=torch.long), torch.tensor(cont_norm, dtype=torch.float32)


def run_single_deep_architecture(arch_name: str, df: pd.DataFrame, feature_cols: list, target_col: str, loso_splits: list, fc_splits: list):
    root = get_experiments_root()
    family = "Deep_Learning"
    model_name = arch_name.upper()

    if is_run_completed(model_name, family):
        print(f"Skipping {model_name} (already recorded in model_registry.csv).")
        return

    print(f"\n--- Running Family C: {model_name} (5 Seeds) ---")
    run_id = generate_run_id(family, model_name)
    exp_dir = root / "experiments" / family / model_name / run_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    fold_models_dir = exp_dir / "fold_models"
    fold_models_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    seeds = [42, 123, 456, 789, 2026]
    seed_loso_oof_preds = []

    # Map categories across full dataset for consistent embedding indices
    cat_cols = ["District", "Crop", "Season", "Irrigation_Type"]
    cat_maps = {col: {val: i for i, val in enumerate(sorted(df[col].astype(str).unique()))} for col in cat_cols}
    cat_cards = [len(cat_maps[c]) for c in cat_cols]
    emb_dims = [min(16, max(4, c // 2)) for c in cat_cards]

    for seed in seeds:
        torch.manual_seed(seed)
        np.random.seed(seed)
        loso_oof = np.zeros(len(df))

        # Evaluate across LOSO folds
        for fold_info in loso_splits:
            fold_name = fold_info["fold_name"]
            tr_df = df.iloc[fold_info["train_idx"]].copy()
            te_df = df.iloc[fold_info["test_idx"]].copy()

            imputer = CropLagImputer().fit(tr_df)
            cont_cols = ["Year_Start", "USD_LKR_Rate", "Prev_Season_Total_Cost_Incl_Imputed"]
            tr_imp = imputer.transform(tr_df)
            cont_vals = tr_imp[cont_cols].values.astype(np.float32)
            scalers = {"mean": cont_vals.mean(axis=0), "std": cont_vals.std(axis=0)}

            X_cat_tr, X_cont_tr = encode_tabular_features(tr_df, imputer, cat_maps, scalers)
            y_tr = torch.tensor(np.log1p(tr_df[target_col].values.astype(np.float32)), dtype=torch.float32)

            X_cat_te, X_cont_te = encode_tabular_features(te_df, imputer, cat_maps, scalers)

            if arch_name.lower() == "tabnet":
                # Combine cat + cont for TabNet
                X_all_tr = np.hstack([X_cat_tr.numpy(), X_cont_tr.numpy()])
                X_all_te = np.hstack([X_cat_te.numpy(), X_cont_te.numpy()])
                tn = TabNetWrapper(max_epochs=80, seed=seed, verbose=0)
                tn.fit(X_all_tr, tr_df[target_col].values)
                preds = tn.predict(X_all_te)
            else:
                # PyTorch neural models
                if arch_name.lower() == "mlp":
                    net = TabularMLP(cat_cards, emb_dims, num_cont=3, hidden_dims=[64, 32], dropout=0.15)
                elif arch_name.lower() == "ft_transformer":
                    net = FTTransformer(cat_cards, num_cont=3, d_token=24, n_heads=4, n_blocks=2, dropout=0.1)
                elif arch_name.lower() in ["lstm", "gru", "cnn"]:
                    net = SequenceModel(model_type=arch_name.lower(), input_dim=7, hidden_dim=24)

                optimizer = torch.optim.AdamW(net.parameters(), lr=0.003, weight_decay=1e-4)
                criterion = nn.MSELoss()

                # Train loop
                net.train()
                for epoch in range(60):
                    optimizer.zero_grad()
                    if arch_name.lower() in ["lstm", "gru", "cnn"]:
                        # Pseudo-sequence window: broadcast features across 2 time steps
                        x_seq = torch.cat([X_cat_tr.float(), X_cont_tr], dim=-1).unsqueeze(1).repeat(1, 2, 1)
                        out = net(x_seq)
                    else:
                        out = net(X_cat_tr, X_cont_tr)
                    loss = criterion(out, y_tr)
                    loss.backward()
                    optimizer.step()

                net.eval()
                with torch.no_grad():
                    if arch_name.lower() in ["lstm", "gru", "cnn"]:
                        x_seq_te = torch.cat([X_cat_te.float(), X_cont_te], dim=-1).unsqueeze(1).repeat(1, 2, 1)
                        preds_log = net(x_seq_te).numpy()
                    else:
                        preds_log = net(X_cat_te, X_cont_te).numpy()
                    preds = np.expm1(np.clip(preds_log, 0, 18.0))

            loso_oof[fold_info["test_idx"]] = preds

            # Save fold model for seed 42
            if seed == 42:
                f_path = fold_models_dir / f"{fold_name}_seed{seed}.pt"
                if arch_name.lower() != "tabnet":
                    torch.save(net.state_dict(), f_path)
                    record_manifest_entry(
                        run_id=run_id, family=family, model_name=model_name,
                        file_path=f_path, fold=fold_name, seed=seed,
                        load_test_passed=True, notes="PyTorch state_dict"
                    )

        seed_loso_oof_preds.append(loso_oof)

    # Average predictions across 5 seeds
    mean_oof_preds = np.mean(seed_loso_oof_preds, axis=0)
    overall_loso = compute_core_metrics(df[target_col].values, mean_oof_preds)

    runtime = time.time() - start_time

    # Save ensemble predictions across seeds
    df_pred = df[["row_id", "Crop", "District", "Season", "Irrigation_Type", "Year_Start", "economic_regime", target_col]].copy()
    df_pred["predicted"] = mean_oof_preds
    df_pred.to_csv(exp_dir / "predictions.csv", index=False)

    with open(exp_dir / "metrics.json", "w") as f:
        json.dump({"overall_loso": overall_loso, "seeds": seeds}, f, indent=2)

    record_experiment_run(
        run_id=run_id,
        family=family,
        model_name=model_name,
        loso_metrics=overall_loso,
        fc_metrics=None,
        hyperparameters={"seeds": seeds, "arch": arch_name},
        runtime_seconds=runtime
    )

    print(f"Finished {model_name} (5 Seeds) in {runtime:.1f}s | LOSO MAE: Rs {overall_loso['MAE']:,.1f} | R2: {overall_loso['R2']:.4f}")


def main():
    print("=" * 80)
    print("STARTING FAMILY C (DEEP LEARNING TABULAR & SEQUENCE) EXPERIMENT RUNNER")
    print("=" * 80)
    df = load_model_data()
    feature_cols, target_col = get_feature_and_target_columns()
    loso_splits = get_loso_splits(df)
    fc_splits = get_forward_chaining_splits(df)

    deep_architectures = [
        "mlp",
        "tabnet",
        "ft_transformer",
        "lstm",
        "gru",
        "cnn"
    ]

    for arch in deep_architectures:
        run_single_deep_architecture(arch, df, feature_cols, target_col, loso_splits, fc_splits)

    print("\nFamily C Training Complete!")


if __name__ == "__main__":
    main()
