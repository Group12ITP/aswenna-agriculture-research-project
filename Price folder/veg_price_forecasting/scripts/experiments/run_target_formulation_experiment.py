import sys
from pathlib import Path
proj_root = Path(__file__).resolve().parent.parent
if str(proj_root) not in sys.path:
    sys.path.insert(0, str(proj_root))

import logging
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import lightgbm as lgb
import xgboost as xgb
from catboost import CatBoostRegressor

from src.utils import load_config, set_seeds, get_logger
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.train import prepare_feature_matrices
from src.metrics import evaluate_predictions, compute_skill_vs_naive
from src.models.deep_learning import MLPNet, GRUNet, TCNNet, NBeatsNet, NHiTSNet, device

logger = get_logger("target_experiment")

def train_dl_model(arch, X_train, y_train, X_val, y_val, X_test, epochs=20, lr=1e-3, batch_size=128):
    """Clean PyTorch model trainer returning val_preds and test_preds."""
    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_train)
    X_vl_s = scaler.transform(X_val)
    X_te_s = scaler.transform(X_test)
    
    y_scaler = StandardScaler()
    y_tr_s = y_scaler.fit_transform(np.array(y_train).reshape(-1, 1)).ravel()
    
    in_dim = X_train.shape[1]
    if arch == "mlp":
        model = MLPNet(in_dim, hidden_dims=(128, 64))
    elif arch == "gru":
        model = GRUNet(in_dim, hidden_dim=64)
    elif arch == "tcn_1d":
        model = TCNNet(in_dim, num_channels=(64, 32))
    elif arch == "nbeats":
        model = NBeatsNet(in_dim, hidden_dim=128)
    elif arch == "nhits":
        model = NHiTSNet(in_dim, hidden_dim=64)
    else:
        raise ValueError(f"Unknown arch {arch}")
        
    model = model.to(device)
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.HuberLoss()
    
    ds = TensorDataset(torch.tensor(X_tr_s, dtype=torch.float32), torch.tensor(y_tr_s, dtype=torch.float32))
    loader = DataLoader(ds, batch_size=batch_size, shuffle=True)
    
    best_loss = float("inf")
    best_w = None
    
    model.train()
    for ep in range(epochs):
        for bx, by in loader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            p = model(bx)
            loss = criterion(p, by)
            loss.backward()
            optimizer.step()
            
    model.eval()
    with torch.no_grad():
        p_vl_norm = model(torch.tensor(X_vl_s, dtype=torch.float32).to(device)).cpu().numpy().reshape(-1, 1)
        val_pred = y_scaler.inverse_transform(p_vl_norm).ravel()
        
    # Refit on train + val for test
    X_tr_val = np.vstack([X_train, X_val])
    y_tr_val = np.concatenate([y_train, y_val])
    
    X_tr_val_s = scaler.fit_transform(X_tr_val)
    X_te_s = scaler.transform(X_test)
    y_tr_val_s = y_scaler.fit_transform(y_tr_val.reshape(-1, 1)).ravel()
    
    # Fresh model for refit
    if arch == "mlp":
        model_final = MLPNet(in_dim, hidden_dims=(128, 64))
    elif arch == "gru":
        model_final = GRUNet(in_dim, hidden_dim=64)
    elif arch == "tcn_1d":
        model_final = TCNNet(in_dim, num_channels=(64, 32))
    elif arch == "nbeats":
        model_final = NBeatsNet(in_dim, hidden_dim=128)
    elif arch == "nhits":
        model_final = NHiTSNet(in_dim, hidden_dim=64)
        
    model_final = model_final.to(device)
    opt_final = optim.AdamW(model_final.parameters(), lr=lr, weight_decay=1e-4)
    ds_final = TensorDataset(torch.tensor(X_tr_val_s, dtype=torch.float32), torch.tensor(y_tr_val_s, dtype=torch.float32))
    loader_final = DataLoader(ds_final, batch_size=batch_size, shuffle=True)
    
    model_final.train()
    for ep in range(epochs):
        for bx, by in loader_final:
            bx, by = bx.to(device), by.to(device)
            opt_final.zero_grad()
            p = model_final(bx)
            loss = criterion(p, by)
            loss.backward()
            opt_final.step()
            
    model_final.eval()
    with torch.no_grad():
        p_te_norm = model_final(torch.tensor(X_te_s, dtype=torch.float32).to(device)).cpu().numpy().reshape(-1, 1)
        test_pred = y_scaler.inverse_transform(p_te_norm).ravel()
        
    return val_pred, test_pred

def run_experiment():
    cfg = load_config()
    set_seeds(42)
    
    df_wide, df_long = load_and_preprocess_vegetables(cfg)
    df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
    train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg)
    
    models = [
        "lasso", "ridge", "elastic_net",
        "lightgbm", "xgboost", "catboost", "extra_trees",
        "mlp", "tcn_1d", "gru", "nbeats", "nhits"
    ]
    
    horizons = [1, 4, 8, 12]
    records = []
    
    for h in horizons:
        print(f"\n{'='*25} TARGET EXPERIMENT: HORIZON h={h} {'='*25}")
        target_col = f"target_h{h}"
        X, y, feature_cols = prepare_feature_matrices(df_feat, target_col=target_col)
        
        y_origin_tr = df_feat.loc[train_mask, "price_lkr"].values
        y_origin_vl = df_feat.loc[val_mask, "price_lkr"].values
        y_origin_te = df_feat.loc[test_mask, "price_lkr"].values
        
        y_tr_true = y[train_mask].values
        y_vl_true = y[val_mask].values
        y_te_true = y[test_mask].values
        
        # Log ratio targets
        r_tr = np.log(np.clip(y_tr_true / np.clip(y_origin_tr, 1.0, None), 1e-4, None))
        r_vl = np.log(np.clip(y_vl_true / np.clip(y_origin_vl, 1.0, None), 1e-4, None))
        r_te = np.log(np.clip(y_te_true / np.clip(y_origin_te, 1.0, None), 1e-4, None))
        
        valid_tr = pd.notna(y_tr_true) & pd.notna(r_tr)
        valid_vl = pd.notna(y_vl_true) & pd.notna(r_vl)
        valid_te = pd.notna(y_te_true) & pd.notna(r_te)
        
        X_tr = X[train_mask].values[valid_tr]
        X_vl = X[val_mask].values[valid_vl]
        X_te = X[test_mask].values[valid_te]
        
        y_tr_lvl = y_tr_true[valid_tr]
        y_vl_lvl = y_vl_true[valid_vl]
        y_te_lvl = y_te_true[valid_te]
        
        r_tr_clean = r_tr[valid_tr]
        r_vl_clean = r_vl[valid_vl]
        r_te_clean = r_te[valid_te]
        
        orig_vl = y_origin_vl[valid_vl]
        orig_te = y_origin_te[valid_te]
        
        y_train_hist = df_feat.loc[train_mask, "price_lkr"]
        y_train_val_hist = df_feat.loc[train_mask | val_mask, "price_lkr"]
        
        # Naive benchmarks
        m_naive_vl = evaluate_predictions(y_vl_lvl, orig_vl, y_train_history=y_train_hist)
        m_naive_te = evaluate_predictions(y_te_lvl, orig_te, y_train_history=y_train_val_hist)
        
        for m_name in models:
            print(f"  Training [{m_name}] for h={h} in both modes...")
            
            # --- MODE A: RAW PRICE LEVEL TARGET ---
            if m_name == "lasso":
                mod_lvl = Pipeline([("scaler", StandardScaler()), ("reg", Lasso(alpha=0.1, random_state=42, max_iter=2000))])
                mod_lvl.fit(X_tr, y_tr_lvl)
                val_p_lvl = mod_lvl.predict(X_vl)
                
                # Refit on train+val
                X_tr_val = np.vstack([X_tr, X_vl])
                y_tr_val = np.concatenate([y_tr_lvl, y_vl_lvl])
                mod_lvl_f = Pipeline([("scaler", StandardScaler()), ("reg", Lasso(alpha=0.1, random_state=42, max_iter=2000))])
                mod_lvl_f.fit(X_tr_val, y_tr_val)
                test_p_lvl = mod_lvl_f.predict(X_te)
                
            elif m_name == "ridge":
                mod_lvl = Pipeline([("scaler", StandardScaler()), ("reg", Ridge(alpha=1.0, random_state=42))])
                mod_lvl.fit(X_tr, y_tr_lvl)
                val_p_lvl = mod_lvl.predict(X_vl)
                
                X_tr_val = np.vstack([X_tr, X_vl])
                y_tr_val = np.concatenate([y_tr_lvl, y_vl_lvl])
                mod_lvl_f = Pipeline([("scaler", StandardScaler()), ("reg", Ridge(alpha=1.0, random_state=42))])
                mod_lvl_f.fit(X_tr_val, y_tr_val)
                test_p_lvl = mod_lvl_f.predict(X_te)
                
            elif m_name == "elastic_net":
                mod_lvl = Pipeline([("scaler", StandardScaler()), ("reg", ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=42, max_iter=2000))])
                mod_lvl.fit(X_tr, y_tr_lvl)
                val_p_lvl = mod_lvl.predict(X_vl)
                
                X_tr_val = np.vstack([X_tr, X_vl])
                y_tr_val = np.concatenate([y_tr_lvl, y_vl_lvl])
                mod_lvl_f = Pipeline([("scaler", StandardScaler()), ("reg", ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=42, max_iter=2000))])
                mod_lvl_f.fit(X_tr_val, y_tr_val)
                test_p_lvl = mod_lvl_f.predict(X_te)
                
            elif m_name == "lightgbm":
                mod_lvl = lgb.LGBMRegressor(n_estimators=120, learning_rate=0.05, num_leaves=31, random_state=42, verbose=-1, n_jobs=-1)
                mod_lvl.fit(X_tr, y_tr_lvl)
                val_p_lvl = mod_lvl.predict(X_vl)
                
                X_tr_val = np.vstack([X_tr, X_vl])
                y_tr_val = np.concatenate([y_tr_lvl, y_vl_lvl])
                mod_lvl_f = lgb.LGBMRegressor(n_estimators=120, learning_rate=0.05, num_leaves=31, random_state=42, verbose=-1, n_jobs=-1)
                mod_lvl_f.fit(X_tr_val, y_tr_val)
                test_p_lvl = mod_lvl_f.predict(X_te)
                
            elif m_name == "xgboost":
                mod_lvl = xgb.XGBRegressor(n_estimators=120, learning_rate=0.05, max_depth=5, random_state=42, n_jobs=-1)
                mod_lvl.fit(X_tr, y_tr_lvl)
                val_p_lvl = mod_lvl.predict(X_vl)
                
                X_tr_val = np.vstack([X_tr, X_vl])
                y_tr_val = np.concatenate([y_tr_lvl, y_vl_lvl])
                mod_lvl_f = xgb.XGBRegressor(n_estimators=120, learning_rate=0.05, max_depth=5, random_state=42, n_jobs=-1)
                mod_lvl_f.fit(X_tr_val, y_tr_val)
                test_p_lvl = mod_lvl_f.predict(X_te)
                
            elif m_name == "catboost":
                mod_lvl = CatBoostRegressor(iterations=120, learning_rate=0.05, depth=5, random_seed=42, verbose=0)
                mod_lvl.fit(X_tr, y_tr_lvl)
                val_p_lvl = mod_lvl.predict(X_vl)
                
                X_tr_val = np.vstack([X_tr, X_vl])
                y_tr_val = np.concatenate([y_tr_lvl, y_vl_lvl])
                mod_lvl_f = CatBoostRegressor(iterations=120, learning_rate=0.05, depth=5, random_seed=42, verbose=0)
                mod_lvl_f.fit(X_tr_val, y_tr_val)
                test_p_lvl = mod_lvl_f.predict(X_te)
                
            elif m_name == "extra_trees":
                mod_lvl = ExtraTreesRegressor(n_estimators=100, max_depth=12, min_samples_leaf=3, random_state=42, n_jobs=-1)
                mod_lvl.fit(X_tr, y_tr_lvl)
                val_p_lvl = mod_lvl.predict(X_vl)
                
                X_tr_val = np.vstack([X_tr, X_vl])
                y_tr_val = np.concatenate([y_tr_lvl, y_vl_lvl])
                mod_lvl_f = ExtraTreesRegressor(n_estimators=100, max_depth=12, min_samples_leaf=3, random_state=42, n_jobs=-1)
                mod_lvl_f.fit(X_tr_val, y_tr_val)
                test_p_lvl = mod_lvl_f.predict(X_te)
                
            else: # Deep learning
                val_p_lvl, test_p_lvl = train_dl_model(m_name, X_tr, y_tr_lvl, X_vl, y_vl_lvl, X_te, epochs=20)
                
            val_p_lvl = np.maximum(0.0, val_p_lvl)
            test_p_lvl = np.maximum(0.0, test_p_lvl)
            
            mets_lvl_val = evaluate_predictions(y_vl_lvl, val_p_lvl, y_train_history=y_train_hist)
            mets_lvl_te = evaluate_predictions(y_te_lvl, test_p_lvl, y_train_history=y_train_val_hist)
            skill_lvl_te = compute_skill_vs_naive(mets_lvl_te["MASE"], m_naive_te["MASE"])
            
            # --- MODE B: LOG PRICE RATIO TARGET ---
            if m_name == "lasso":
                mod_rat = Pipeline([("scaler", StandardScaler()), ("reg", Lasso(alpha=0.01, random_state=42, max_iter=2000))])
                mod_rat.fit(X_tr, r_tr_clean)
                r_pred_vl = mod_rat.predict(X_vl)
                
                X_tr_val = np.vstack([X_tr, X_vl])
                r_tr_val = np.concatenate([r_tr_clean, r_vl_clean])
                mod_rat_f = Pipeline([("scaler", StandardScaler()), ("reg", Lasso(alpha=0.01, random_state=42, max_iter=2000))])
                mod_rat_f.fit(X_tr_val, r_tr_val)
                r_pred_te = mod_rat_f.predict(X_te)
                
            elif m_name == "ridge":
                mod_rat = Pipeline([("scaler", StandardScaler()), ("reg", Ridge(alpha=1.0, random_state=42))])
                mod_rat.fit(X_tr, r_tr_clean)
                r_pred_vl = mod_rat.predict(X_vl)
                
                X_tr_val = np.vstack([X_tr, X_vl])
                r_tr_val = np.concatenate([r_tr_clean, r_vl_clean])
                mod_rat_f = Pipeline([("scaler", StandardScaler()), ("reg", Ridge(alpha=1.0, random_state=42))])
                mod_rat_f.fit(X_tr_val, r_tr_val)
                r_pred_te = mod_rat_f.predict(X_te)
                
            elif m_name == "elastic_net":
                mod_rat = Pipeline([("scaler", StandardScaler()), ("reg", ElasticNet(alpha=0.01, l1_ratio=0.5, random_state=42, max_iter=2000))])
                mod_rat.fit(X_tr, r_tr_clean)
                r_pred_vl = mod_rat.predict(X_vl)
                
                X_tr_val = np.vstack([X_tr, X_vl])
                r_tr_val = np.concatenate([r_tr_clean, r_vl_clean])
                mod_rat_f = Pipeline([("scaler", StandardScaler()), ("reg", ElasticNet(alpha=0.01, l1_ratio=0.5, random_state=42, max_iter=2000))])
                mod_rat_f.fit(X_tr_val, r_tr_val)
                r_pred_te = mod_rat_f.predict(X_te)
                
            elif m_name == "lightgbm":
                mod_rat = lgb.LGBMRegressor(n_estimators=120, learning_rate=0.05, num_leaves=31, random_state=42, verbose=-1, n_jobs=-1)
                mod_rat.fit(X_tr, r_tr_clean)
                r_pred_vl = mod_rat.predict(X_vl)
                
                X_tr_val = np.vstack([X_tr, X_vl])
                r_tr_val = np.concatenate([r_tr_clean, r_vl_clean])
                mod_rat_f = lgb.LGBMRegressor(n_estimators=120, learning_rate=0.05, num_leaves=31, random_state=42, verbose=-1, n_jobs=-1)
                mod_rat_f.fit(X_tr_val, r_tr_val)
                r_pred_te = mod_rat_f.predict(X_te)
                
            elif m_name == "xgboost":
                mod_rat = xgb.XGBRegressor(n_estimators=120, learning_rate=0.05, max_depth=5, random_state=42, n_jobs=-1)
                mod_rat.fit(X_tr, r_tr_clean)
                r_pred_vl = mod_rat.predict(X_vl)
                
                X_tr_val = np.vstack([X_tr, X_vl])
                r_tr_val = np.concatenate([r_tr_clean, r_vl_clean])
                mod_rat_f = xgb.XGBRegressor(n_estimators=120, learning_rate=0.05, max_depth=5, random_state=42, n_jobs=-1)
                mod_rat_f.fit(X_tr_val, r_tr_val)
                r_pred_te = mod_rat_f.predict(X_te)
                
            elif m_name == "catboost":
                mod_rat = CatBoostRegressor(iterations=120, learning_rate=0.05, depth=5, random_seed=42, verbose=0)
                mod_rat.fit(X_tr, r_tr_clean)
                r_pred_vl = mod_rat.predict(X_vl)
                
                X_tr_val = np.vstack([X_tr, X_vl])
                r_tr_val = np.concatenate([r_tr_clean, r_vl_clean])
                mod_rat_f = CatBoostRegressor(iterations=120, learning_rate=0.05, depth=5, random_seed=42, verbose=0)
                mod_rat_f.fit(X_tr_val, r_tr_val)
                r_pred_te = mod_rat_f.predict(X_te)
                
            elif m_name == "extra_trees":
                mod_rat = ExtraTreesRegressor(n_estimators=100, max_depth=12, min_samples_leaf=3, random_state=42, n_jobs=-1)
                mod_rat.fit(X_tr, r_tr_clean)
                r_pred_vl = mod_rat.predict(X_vl)
                
                X_tr_val = np.vstack([X_tr, X_vl])
                r_tr_val = np.concatenate([r_tr_clean, r_vl_clean])
                mod_rat_f = ExtraTreesRegressor(n_estimators=100, max_depth=12, min_samples_leaf=3, random_state=42, n_jobs=-1)
                mod_rat_f.fit(X_tr_val, r_tr_val)
                r_pred_te = mod_rat_f.predict(X_te)
                
            else: # Deep learning
                r_pred_vl, r_pred_te = train_dl_model(m_name, X_tr, r_tr_clean, X_vl, r_vl_clean, X_te, epochs=20)
                
            # Reconstruct level forecasts: y_hat = y_origin * exp(r_hat)
            val_p_rat = np.maximum(0.0, orig_vl * np.exp(np.clip(r_pred_vl, -3.0, 3.0)))
            test_p_rat = np.maximum(0.0, orig_te * np.exp(np.clip(r_pred_te, -3.0, 3.0)))
            
            mets_rat_val = evaluate_predictions(y_vl_lvl, val_p_rat, y_train_history=y_train_hist)
            mets_rat_te = evaluate_predictions(y_te_lvl, test_p_rat, y_train_history=y_train_val_hist)
            skill_rat_te = compute_skill_vs_naive(mets_rat_te["MASE"], m_naive_te["MASE"])
            
            # Select target mode strictly on VALIDATION MASE
            chosen_mode = "log_ratio" if mets_rat_val["MASE"] < mets_lvl_val["MASE"] else "raw_level"
            val_mase_gain = (1.0 - mets_rat_val["MASE"] / mets_lvl_val["MASE"]) * 100.0
            
            records.append({
                "model": m_name,
                "horizon": h,
                "val_MASE_level": round(mets_lvl_val["MASE"], 4),
                "val_sMAPE_level": round(mets_lvl_val["sMAPE"], 2),
                "val_MASE_ratio": round(mets_rat_val["MASE"], 4),
                "val_sMAPE_ratio": round(mets_rat_val["sMAPE"], 2),
                "chosen_target_mode": chosen_mode,
                "val_MASE_gain_pct": round(val_mase_gain, 2),
                "test_MASE_level": round(mets_lvl_te["MASE"], 4),
                "test_sMAPE_level": round(mets_lvl_te["sMAPE"], 2),
                "test_skill_level": round(skill_lvl_te, 2),
                "test_MASE_ratio": round(mets_rat_te["MASE"], 4),
                "test_sMAPE_ratio": round(mets_rat_te["sMAPE"], 2),
                "test_skill_ratio": round(skill_rat_te, 2)
            })
            print(f"    Val MASE: Level={mets_lvl_val['MASE']:.4f} vs Ratio={mets_rat_val['MASE']:.4f} -> Chosen: [{chosen_mode}] (Gain: {val_mase_gain:+.2f}%)")

    df_out = pd.DataFrame(records)
    out_csv = Path("results/tables/target_formulation_comparison.csv")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(out_csv, index=False)
    print(f"\nSaved target formulation experiment results to {out_csv}")
    print("\nSummary Table:")
    print(df_out[["model", "horizon", "val_MASE_level", "val_MASE_ratio", "chosen_target_mode", "val_MASE_gain_pct", "test_skill_level", "test_skill_ratio"]].to_string())

if __name__ == "__main__":
    run_experiment()
