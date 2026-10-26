import pandas as pd
import numpy as np

def regenerate_target_formulation_table():
    lead_path = "experiments/leaderboard.csv"
    out_path = "results/tables/target_formulation_comparison.csv"
    
    df_lead = pd.read_csv(lead_path)
    
    horizons = [1, 4, 8, 12]
    models_with_ratio = df_lead[df_lead["target_mode"] == "log_ratio"]["model"].unique()
    
    records = []
    
    for h in horizons:
        h_df = df_lead[df_lead["horizon"] == h]
        naive_row = h_df[(h_df["model"] == "naive") & (h_df["split"] == "test")].iloc[0]
        naive_te_mase = naive_row["MASE"]
        
        for m in sorted(models_with_ratio):
            # Val rows
            val_lvl = h_df[(h_df["model"] == m) & (h_df["split"] == "validation") & (h_df["target_mode"] == "raw_level")]
            val_rat = h_df[(h_df["model"] == m) & (h_df["split"] == "validation") & (h_df["target_mode"] == "log_ratio")]
            
            # Test rows
            te_lvl = h_df[(h_df["model"] == m) & (h_df["split"] == "test") & (h_df["target_mode"] == "raw_level")]
            te_rat = h_df[(h_df["model"] == m) & (h_df["split"] == "test") & (h_df["target_mode"] == "log_ratio")]
            
            if len(val_lvl) == 0 or len(val_rat) == 0:
                continue
                
            vl_m = val_lvl.iloc[0]["MASE"]
            vl_s = val_lvl.iloc[0]["sMAPE"]
            vr_m = val_rat.iloc[0]["MASE"]
            vr_s = val_rat.iloc[0]["sMAPE"]
            
            chosen = "log_ratio" if vr_m < vl_m else "raw_level"
            gain = (1.0 - min(vr_m, vl_m) / max(vr_m, vl_m)) * 100.0
            
            tl_m = te_lvl.iloc[0]["MASE"]
            tl_s = te_lvl.iloc[0]["sMAPE"]
            tl_sk = te_lvl.iloc[0]["Skill_vs_Naive"]
            
            tr_m = te_rat.iloc[0]["MASE"]
            tr_s = te_rat.iloc[0]["sMAPE"]
            tr_sk = te_rat.iloc[0]["Skill_vs_Naive"]
            
            records.append({
                "model": m,
                "horizon": h,
                "val_MASE_level": round(vl_m, 4),
                "val_sMAPE_level": round(vl_s, 2),
                "val_MASE_ratio": round(vr_m, 4),
                "val_sMAPE_ratio": round(vr_s, 2),
                "chosen_target_mode": chosen,
                "val_MASE_gain_pct": round(gain, 2),
                "test_MASE_level": round(tl_m, 4),
                "test_sMAPE_level": round(tl_s, 2),
                "test_skill_level": round(tl_sk, 2),
                "test_MASE_ratio": round(tr_m, 4),
                "test_sMAPE_ratio": round(tr_s, 2),
                "test_skill_ratio": round(tr_sk, 2)
            })
            
    df_out = pd.DataFrame(records)
    df_out.to_csv(out_path, index=False)
    print(f"SUCCESS: Regenerated {out_path} with {len(df_out)} rows from leaderboard.csv.")
    
    # Print h=4 slice
    print("\nHorizon h=4 Target Formulation Comparison:")
    print(df_out[df_out["horizon"] == 4][["model", "val_MASE_level", "val_MASE_ratio", "chosen_target_mode", "val_MASE_gain_pct", "test_MASE_level", "test_MASE_ratio", "test_skill_ratio"]].to_string(index=False))

if __name__ == "__main__":
    regenerate_target_formulation_table()
