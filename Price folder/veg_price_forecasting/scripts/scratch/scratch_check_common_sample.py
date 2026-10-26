import pandas as pd
import numpy as np
from pathlib import Path
from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.models.baselines import NaiveForecaster
from src.metrics import compute_mase, evaluate_predictions, diebold_mariano_test, block_bootstrap_mase

cfg = load_config("config.yaml")
df_wide, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
df_lead = pd.read_csv("experiments/leaderboard.csv")

results = []

for h in [1, 4, 8, 12]:
    train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg, horizon=h)
    target_col = f"target_h{h}"
    target_week = df_feat["week_index"] + h
    max_allowed = 417 - h
    refit_mask = train_mask | (val_mask & (target_week <= max_allowed))
    
    # Load naive test predictions
    test_preds_list = []
    for veg in df_feat["product_name"].unique():
        v_df = df_feat[df_feat["product_name"] == veg].sort_values("week_index")
        train_prices = v_df.loc[train_mask.loc[v_df.index], "price_lkr"].values
        model = NaiveForecaster()
        model.fit(train_prices)
        for idx in v_df.index[test_mask.loc[v_df.index]]:
            curr_w = v_df.loc[idx, "week_index"]
            hist = v_df.loc[v_df["week_index"] <= curr_w, "price_lkr"].values
            test_preds_list.append((idx, model.predict(horizon=h, y_history=hist)))
            
    naive_test_p = pd.Series({idx: p for idx, p in test_preds_list}, name="pred_naive")
    y_test_true = df_feat.loc[test_mask, target_col]
    
    print(f"\n=================== HORIZON h={h} ===================")
    for m_name in ["auto_arima", "sarimax", "prophet"]:
        lead_row = df_lead[(df_lead['split']=='test') & (df_lead['horizon']==h) & (df_lead['model']==m_name)].iloc[0]
        
        runs = sorted(list(Path("experiments/runs").glob(f"*_{m_name}_h{h}")))
        if not runs:
            continue
        p_file = runs[-1] / "predictions_test.csv"
        df_p = pd.read_csv(p_file)
        
        df_eval = df_feat.loc[test_mask, ["product_name", "approx_date", "week_index"]].copy()
        df_eval[target_col] = y_test_true.values
        df_eval["naive_pred"] = naive_test_p.values
        
        df_merged = pd.merge(df_eval.reset_index(), df_p[["product_name", "approx_date", "y_pred"]], on=["product_name", "approx_date"], how="left").set_index("index")
        
        model_pred = df_merged["y_pred"]
        
        common_mask = pd.notna(df_merged[target_col]) & pd.notna(model_pred) & pd.notna(df_merged["naive_pred"])
        n_common = int(common_mask.sum())
        
        yt_c = df_merged.loc[common_mask, target_col].values
        yp_c = model_pred.loc[common_mask].values
        yn_c = df_merged.loc[common_mask, "naive_pred"].values
        weeks_c = df_merged.loc[common_mask, "week_index"].values
        
        mets_m = evaluate_predictions(yt_c, yp_c, y_train_history=df_feat.loc[refit_mask, "price_lkr"])
        mets_n = evaluate_predictions(yt_c, yn_c, y_train_history=df_feat.loc[refit_mask, "price_lkr"])
        
        skill_common = round(float((1.0 - mets_m["MASE"] / mets_n["MASE"]) * 100.0), 2)
        
        dm_stat, dm_pval = diebold_mariano_test(yt_c, yp_c, yn_c, h=h, week_indices=weeks_c)
        boot = block_bootstrap_mase(yt_c, yp_c, y_naive_pred=yn_c, y_train_history=df_feat.loc[refit_mask, "price_lkr"], week_indices=weeks_c, block_length=4, n_boot=250)
        
        results.append({
            "horizon": h,
            "model": m_name,
            "n_obs": n_common,
            "model_MAE": mets_m["MAE"],
            "model_MASE": mets_m["MASE"],
            "naive_MASE_common": mets_n["MASE"],
            "skill_vs_naive": skill_common,
            "diff_naive_ci_low": boot.get("diff_naive_ci_low"),
            "diff_naive_ci_high": boot.get("diff_naive_ci_high"),
            "DM_stat": dm_stat,
            "DM_pval": dm_pval
        })
        
        print(f"Model: {m_name} (n={n_common}):")
        print(f"  Leaderboard: MASE={lead_row['MASE']:.4f}, skill={lead_row['Skill_vs_Naive']:+.2f}%, DM_stat={lead_row['DM_stat_vs_Naive']}, DM_pval={lead_row['DM_pval_vs_Naive']}")
        print(f"  Common Sample: Model MASE={mets_m['MASE']:.4f}, Naive MASE={mets_n['MASE']:.4f}")
        print(f"  Common Skill: {skill_common:+.2f}%")
        print(f"  Common DM: stat={dm_stat:.4f}, pval={dm_pval:.4f}")
        print(f"  Common Diff Naive CI: [{boot.get('diff_naive_ci_low')}, {boot.get('diff_naive_ci_high')}]")

df_res = pd.DataFrame(results)
df_res.to_csv("results/tables/statistical_models_common_sample.csv", index=False)
print("\nSaved results/tables/statistical_models_common_sample.csv")
