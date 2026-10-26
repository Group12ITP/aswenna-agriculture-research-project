import json
from pathlib import Path
import pandas as pd
import numpy as np

def run_selection():
    df_lead = pd.read_csv("experiments/leaderboard.csv")
    baselines = ["naive", "drift", "moving_average_4", "moving_average_12", "seasonal_naive_48"]
    
    def get_tier(m):
        if m in ["linear_regression", "ridge", "lasso", "elastic_net", "auto_arima", "sarimax", "holt_winters_ets", "prophet"]:
            return (1, "Linear/Statistical")
        elif m in ["lightgbm", "xgboost", "catboost", "random_forest", "extra_trees", "gradient_boosting", "svr"]:
            return (2, "Tree/Ensemble ML")
        elif m in ["mlp", "lstm", "gru", "tcn_1d", "nbeats", "transformer", "nhits", "tft_lite"]:
            return (3, "Deep Learning")
        elif m in ["simple_average_top3", "stacking_meta_learner", "best_per_category"]:
            return (4, "Ensemble Paradigm")
        return (99, "Other")

    selection_records = []
    selected_manifest = {}
    horizons = [1, 4, 8, 12]
    
    print("=" * 80)
    print("PRE-REGISTERED 1-SE MODEL SELECTION WITH RESTORED VALIDATION CIs")
    print("=" * 80)

    for h in horizons:
        # Candidate set: exclude baselines
        sub = df_lead[(df_lead["horizon"] == h) & (df_lead["split"] == "validation")].copy()
        sub = sub[~sub["model"].isin(baselines)]
        
        # Filter each model to its chosen mode on validation
        valid_candidates = []
        for m in sub["model"].unique():
            m_rows = sub[sub["model"] == m]
            best_mode_row = m_rows.sort_values("MASE").iloc[0]
            valid_candidates.append(best_mode_row)
            
        cands = pd.DataFrame(valid_candidates)
        cands["tier"] = cands["model"].apply(lambda m: get_tier(m)[0])
        cands["tier_name"] = cands["model"].apply(lambda m: get_tier(m)[1])
        cands = cands.sort_values("MASE").reset_index(drop=True)
        
        best = cands.iloc[0]
        best_m = best["MASE"]
        
        # Parse SE directly from the restored validation MASE_CI_95 of the best model
        ci_str = str(best["MASE_CI_95"]).strip("[]")
        ci_low, ci_high = [float(x) for x in ci_str.split(",")]
        se_val = (ci_high - ci_low) / (2.0 * 1.96)
        thresh = best_m + se_val
        
        in_band = cands[cands["MASE"] <= thresh].sort_values(["tier", "MASE"]).reset_index(drop=True)
        chosen = in_band.iloc[0]
        
        # Test performance of chosen model
        test_chosen = df_lead[(df_lead["horizon"] == h) & (df_lead["split"] == "test") & (df_lead["model"] == chosen["model"]) & (df_lead["target_mode"] == chosen["target_mode"])].iloc[0]
        
        print(f"\n>>> Horizon h={h:2d} <<<")
        print(f"  Best Val Model: {best['model']} ({best['target_mode']}, Tier {best['tier']} - {best['tier_name']})")
        print(f"  Best Val MASE:  {best_m:.4f} | 95% Val CI: [{ci_low:.4f}, {ci_high:.4f}] | Bootstrap SE: {se_val:.4f}")
        print(f"  1-SE Selection Band: [{best_m:.4f}, {thresh:.4f}] (contains {len(in_band)} eligible models)")
        print("  Eligible Candidates in Band:")
        for _, r in in_band.iterrows():
            print(f"    * {r['model']:22s} ({r['target_mode']:9s}) | Tier {r['tier']} ({r['tier_name']:18s}) | Val MASE: {r['MASE']:.4f}")
            
        print(f"  >> SELECTED MODEL: {chosen['model']} ({chosen['target_mode']})")
        print(f"     Tier:             {chosen['tier_name']}")
        print(f"     Val MASE:         {chosen['MASE']:.4f}")
        print(f"     Test MASE:        {test_chosen['MASE']:.4f}")
        print(f"     Test Skill:       {test_chosen['Skill_vs_Naive']:+.2f}%")
        print(f"     Holm-adj p-val:   {test_chosen['DM_pval_Holm_vs_Naive']:.4f} (Significant: {test_chosen['DM_pval_Holm_vs_Naive'] < 0.05})")

        selected_manifest[f"h{h}"] = {
            "model": chosen["model"],
            "target_mode": chosen["target_mode"],
            "tier": chosen["tier_name"],
            "val_mase": round(float(chosen["MASE"]), 4),
            "band": [round(float(best_m), 4), round(float(thresh), 4)],
            "test_mase": round(float(test_chosen["MASE"]), 4),
            "test_skill": round(float(test_chosen["Skill_vs_Naive"]), 2),
            "holm_p": round(float(test_chosen["DM_pval_Holm_vs_Naive"]), 4)
        }
        
        selection_records.append({
            "horizon": h,
            "best_model": best["model"],
            "best_target_mode": best["target_mode"],
            "best_val_mase": round(float(best_m), 4),
            "best_mase_ci": f"[{ci_low:.4f}, {ci_high:.4f}]",
            "se_val": round(float(se_val), 4),
            "band_lower": round(float(best_m), 4),
            "band_upper": round(float(thresh), 4),
            "n_in_band": len(in_band),
            "selected_model": chosen["model"],
            "selected_target_mode": chosen["target_mode"],
            "selected_tier": chosen["tier_name"],
            "selected_val_mase": round(float(chosen["MASE"]), 4),
            "selected_test_mase": round(float(test_chosen["MASE"]), 4),
            "selected_test_skill": round(float(test_chosen["Skill_vs_Naive"]), 2),
            "selected_test_holm_p": round(float(test_chosen["DM_pval_Holm_vs_Naive"]), 4)
        })

    df_sel = pd.DataFrame(selection_records)
    df_sel.to_csv("results/tables/model_selection_bands.csv", index=False)
    print("\nSaved results/tables/model_selection_bands.csv")
    
    # Update run manifest
    manifest_path = Path("experiments/run_manifest.json")
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    manifest["selected_models_by_horizon"] = selected_manifest
    manifest["primary_selected_model"] = selected_manifest["h4"]["model"]
    manifest["primary_selected_target_mode"] = selected_manifest["h4"]["target_mode"]
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("Updated experiments/run_manifest.json")

    # Audit Holm significance across all models on test
    print("\n" + "=" * 80)
    print("HOLM SIGNIFICANCE SUMMARY ACROSS ALL MODELS (alpha=0.05)")
    print("=" * 80)
    test_df = df_lead[df_lead["split"] == "test"]
    for h in horizons:
        h_test = test_df[test_df["horizon"] == h]
        sig_count = (h_test["DM_pval_Holm_vs_Naive"] < 0.05).sum()
        total_tests = len(h_test)
        print(f"Horizon h={h:2d}: {sig_count}/{total_tests} models are Holm-significant vs naive persistence.")
        if sig_count > 0:
            sig_models = h_test[h_test["DM_pval_Holm_vs_Naive"] < 0.05][["model", "target_mode", "Skill_vs_Naive", "DM_pval_Holm_vs_Naive"]]
            print(f"  Significant models:\n{sig_models.to_string(index=False)}")

if __name__ == "__main__":
    run_selection()
