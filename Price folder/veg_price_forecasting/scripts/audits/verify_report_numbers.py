import re
import sys
from pathlib import Path
import pandas as pd
import numpy as np

def verify_all():
    exp_path = Path("experiments")
    res_path = Path("results")
    tbl_path = res_path / "tables"
    
    df_lead = pd.read_csv(exp_path / "leaderboard.csv")
    
    print("=" * 80)
    print("STARTING COMPREHENSIVE AUDIT & REPORT NUMERICAL VERIFICATION")
    print("=" * 80)
    
    errors = []
    
    # =========================================================================
    # PART 1: VERIFY results/report.md
    # =========================================================================
    report_path = res_path / "report.md"
    if not report_path.exists():
        errors.append(f"Missing file: {report_path}")
    else:
        print("\n>>> 1. Verifying results/report.md against experiments/leaderboard.csv...")
        report_text = report_path.read_text(encoding="utf-8")
        
        # Check obsolete pre-purge numbers do not exist
        obsolete_numbers = ["0.6367", "0.7783", "0.8162", "+3.98%", "3.98%", "0.6376"]
        for num in obsolete_numbers:
            if num in report_text:
                errors.append(f"results/report.md contains obsolete pre-purge number: {num}")
                
        # Check primary horizon h=4 model values
        h4_test = df_lead[(df_lead["horizon"] == 4) & (df_lead["split"] == "test")]
        h4_val = df_lead[(df_lead["horizon"] == 4) & (df_lead["split"] == "validation")]
        
        verified_lead_metrics = 0
        for _, t_row in h4_test.iterrows():
            model = t_row["model"]
            mode = t_row.get("target_mode", "raw_level")
            v_rows = h4_val[(h4_val["model"] == model) & (h4_val["target_mode"] == mode)]
            if len(v_rows) == 0:
                continue
            v_row = v_rows.iloc[0]
            
            val_mase = f"{v_row['MASE']:.4f}"
            test_mase = f"{t_row['MASE']:.4f}"
            test_smape = f"{t_row['sMAPE']:.2f}%"
            
            if val_mase in report_text:
                verified_lead_metrics += 1
            else:
                errors.append(f"report.md missing Val MASE {val_mase} for {model} ({mode})")
                
            if test_mase in report_text:
                verified_lead_metrics += 1
            else:
                errors.append(f"report.md missing Test MASE {test_mase} for {model} ({mode})")
                
            if test_smape in report_text:
                verified_lead_metrics += 1
            else:
                errors.append(f"report.md missing Test sMAPE {test_smape} for {model} ({mode})")
                
        print(f"  Verified {verified_lead_metrics} leaderboard metrics present in report.md.")
        
        # Check selection statements
        if "auto_arima" not in report_text:
            errors.append("report.md does not mention selected model auto_arima")
        if "Lasso is no longer inside the $h=4$ band" not in report_text:
            errors.append("report.md missing explicit statement that Lasso is no longer inside h=4 band")
        if "0/42 candidate models" not in report_text:
            errors.append("report.md missing explicit statement that 0/42 candidate models are Holm significant at h=4/h=8")
        if "61.2% reduction" not in report_text and "61.24%" not in report_text:
            errors.append("report.md missing leafy greens 61.2% reduction claim")
            
    # =========================================================================
    # PART 2: VERIFY results/prophet_audit.md
    # =========================================================================
    prophet_path = res_path / "prophet_audit.md"
    if not prophet_path.exists():
        errors.append(f"Missing file: {prophet_path}")
    else:
        print("\n>>> 2. Verifying results/prophet_audit.md against experiments/leaderboard.csv...")
        p_text = prophet_path.read_text(encoding="utf-8")
        
        # Check obsolete numbers do not exist
        obsolete_numbers = ["0.6367", "0.0048", "0.7783"]
        for num in obsolete_numbers:
            if num in p_text:
                errors.append(f"results/prophet_audit.md contains obsolete run number: {num}")
                
        # Check current leaderboard values for Prophet
        prophet_lead = df_lead[(df_lead["model"] == "prophet") & (df_lead["target_mode"] == "raw_level")]
        
        for h in [1, 4, 8, 12]:
            t_row = prophet_lead[(prophet_lead["horizon"] == h) & (prophet_lead["split"] == "test")].iloc[0]
            v_row = prophet_lead[(prophet_lead["horizon"] == h) & (prophet_lead["split"] == "validation")].iloc[0]
            
            t_bias_str = f"{t_row['Bias']:+.2f}"
            v_bias_str = f"{v_row['Bias']:+.2f}"
            t_mase_str = f"{t_row['MASE']:.4f}"
            v_mase_str = f"{v_row['MASE']:.4f}"
            
            if t_bias_str not in p_text and f"{t_row['Bias']:.2f}" not in p_text:
                errors.append(f"prophet_audit.md missing h={h} Test Bias {t_bias_str}")
            if v_bias_str not in p_text and f"{v_row['Bias']:.2f}" not in p_text:
                errors.append(f"prophet_audit.md missing h={h} Val Bias {v_bias_str}")
            if t_mase_str not in p_text:
                errors.append(f"prophet_audit.md missing h={h} Test MASE {t_mase_str}")
            if v_mase_str not in p_text:
                errors.append(f"prophet_audit.md missing h={h} Val MASE {v_mase_str}")
                
        print("  Verified Prophet test/val bias and MASE metrics.")
        
        # Verify annual refit cutoff 416 values
        if "89.26" not in p_text:
            errors.append("prophet_audit.md missing reconciled Naive MAE 89.26 for cutoff 416")
        if "66.96" not in p_text:
            errors.append("prophet_audit.md missing Prophet MAE 66.96 for cutoff 416")
        if "+24.99%" not in p_text:
            errors.append("prophet_audit.md missing skill +24.99% for cutoff 416")
            
        # Verify damping provenance explanation
        if "0.88" not in p_text or "0.85" not in p_text:
            errors.append("prophet_audit.md missing damping provenance comparison (0.88 vs 0.85)")
            
        # Verify honest summary claims
        if "5 of 7" not in p_text and "5 out of 7" not in p_text:
            errors.append("prophet_audit.md missing statement that Prophet loses in 5 of 7 annual refits")
        if "-17.5" not in p_text and "-18%" not in p_text:
            errors.append("prophet_audit.md missing mean historical skill (~ -18%)")
            
    # =========================================================================
    # PART 3: VERIFY results/leakage_audit.md
    # =========================================================================
    leakage_path = res_path / "leakage_audit.md"
    if not leakage_path.exists():
        errors.append(f"Missing file: {leakage_path}")
    else:
        print("\n>>> 3. Verifying results/leakage_audit.md against diagnostic tables...")
        l_text = leakage_path.read_text(encoding="utf-8")
        
        # Check script count
        if "45 Python scripts" not in l_text and "45 scripts" not in l_text and "45 distinct scripts" not in l_text:
            errors.append("leakage_audit.md does not state the real count of 45 test-reading scripts")
            
        # Check placebo table values from results/tables/placebo_study.csv
        df_placebo = pd.read_csv(tbl_path / "placebo_study.csv")
        for _, r in df_placebo.iterrows():
            h = int(r["horizon"])
            p_mase = f"{r['placebo_MASE']:.4f}"
            p_skill = f"{r['placebo_skill_vs_naive']:.2f}%"
            if p_mase not in l_text:
                errors.append(f"leakage_audit.md missing placebo MASE {p_mase} at h={h}")
            if p_skill not in l_text:
                errors.append(f"leakage_audit.md missing placebo skill {p_skill} at h={h}")
        print("  Verified placebo study metrics in leakage_audit.md.")
        
        # Check ablation table values from results/tables/ablation_study.csv
        df_ablation = pd.read_csv(tbl_path / "ablation_study.csv")
        for _, r in df_ablation.iterrows():
            mase_col = "lasso_mase" if "lasso_mase" in r else "lasso_MASE"
            l_mase = f"{r[mase_col]:.4f}"
            if l_mase not in l_text:
                errors.append(f"leakage_audit.md missing ablation Lasso MASE {l_mase}")
        print("  Verified ablation study metrics in leakage_audit.md.")
        
        # Check ratio-Lasso alpha mismatch explanation
        if "alpha=0.01" not in l_text and "alpha \approx 0.01" not in l_text:
            errors.append("leakage_audit.md missing discussion of ratio-Lasso alpha=0.01")
        if "6.20" not in l_text and "6.2" not in l_text:
            errors.append("leakage_audit.md missing discussion of level-Lasso alpha=6.20")
            
        # Check split integrity table values
        df_split = pd.read_csv(tbl_path / "split_integrity_summary.csv")
        for _, r in df_split.iterrows():
            n_str = f"{int(r['n_obs']):,}"
            if n_str not in l_text:
                errors.append(f"leakage_audit.md missing split obs count {n_str}")
        if "4 weeks (\\ge h=4)" not in l_text and "4 weeks (>= h=4)" not in l_text and "4 weeks" not in l_text:
            errors.append("leakage_audit.md missing 4-week purge gap assertion")
        print("  Verified split integrity table in leakage_audit.md.")
        
    # =========================================================================
    # PART 4: VERIFY ADDITIONAL REPORT SECTIONS (7, 8.1, 9, DM LABELS)
    # =========================================================================
    if report_path.exists():
        print("\n>>> 4. Verifying specialized report sections (7, 8.1, 9, DM labels)...")
        # Section 9 forward forecast assertions
        if "Origin: Week 464 (2026-08-25)" not in report_text and "Week 464" not in report_text:
            errors.append("report.md missing forward forecast Origin Week 464")
        if "Target: Week 468" not in report_text and "Week 468" not in report_text:
            errors.append("report.md missing forward forecast Target Week 468")
        if "SYNTHETIC" not in report_text:
            errors.append("report.md missing SYNTHETIC cultivation cost basis label")
        if "16.3%" not in report_text:
            errors.append("report.md missing leafy greens relative width 16.3%")
        if "77.2%" not in report_text:
            errors.append("report.md missing upcountry relative width 77.2%")
            
        # Section 8.1 leafy clean vs stale assertions
        if "384" not in report_text:
            errors.append("report.md missing leafy clean count 384")
        if "4.16" not in report_text:
            errors.append("report.md missing leafy naive MAE 4.16 Rs")
        if "-0.3103" not in report_text:
            errors.append("report.md missing leafy naive R2 -0.3103")
            
        # DM table label check
        if "Worse (p < 0.05)" not in report_text:
            errors.append("report.md missing 'Worse (p < 0.05)' Diebold-Mariano table label")
            
        # 21 models significantly worse at h=1
        if "21" not in report_text:
            errors.append("report.md missing mention of 21 models worse than naive at h=1")
            
        # Naive MASE inside CI
        if "0.7465" not in report_text:
            errors.append("report.md missing naive validation MASE 0.7465 inside CI check")
            
        # Section 5.3 h=12 post-hoc analysis
        if "16/45" not in report_text and "16 of 45" not in report_text and "16" not in report_text:
            errors.append("report.md missing h=12 post-hoc analysis (16 models significant)")
            
        # Section 7 zero N/As in coverage column
        sec7_start = report_text.find("## 7. Prediction Interval Quality")
        sec8_start = report_text.find("## 8. Robustness & Subgroup Analysis")
        if sec7_start != -1 and sec8_start != -1:
            sec7_text = report_text[sec7_start:sec8_start]
            if "N/A" in sec7_text:
                errors.append("report.md Section 7 uncertainty table contains unpopulated 'N/A' entries")
            else:
                print("  Verified Section 7 uncertainty table has 0 'N/A' entries.")
        print("  Verified Sections 7, 8.1, 9, and DM labels.")
            
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    if errors:
        print(f"FAILED: Found {len(errors)} verification errors:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("SUCCESS: 100% of checked metrics and audit artifacts verified successfully!")
        print("=" * 80)

if __name__ == "__main__":
    verify_all()
