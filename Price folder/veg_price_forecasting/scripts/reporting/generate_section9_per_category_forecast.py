import json
from pathlib import Path
import numpy as np
import pandas as pd

from src.utils import load_config, set_seeds
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.models.statistical import AutoARIMARollingForecaster

def run_forward_forecast():
    cfg = load_config()
    set_seeds(42)
    
    df_wide, df_long = load_and_preprocess_vegetables(cfg)
    df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
    
    h = 4
    target_col = f"target_h{h}"
    
    train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg, horizon=h)
    
    # Split val into tuning and calibration
    val_weeks = np.sort(df_feat.loc[val_mask, "week_index"].unique())
    val_cal_weeks = val_weeks[len(val_weeks)//2:]
    val_cal_mask = val_mask & df_feat["week_index"].isin(val_cal_weeks)
    
    print(f"Val Cal weeks: {val_cal_weeks.min()} to {val_cal_weeks.max()} (N={val_cal_mask.sum()})")
    print(f"Test weeks: {df_feat.loc[test_mask, 'week_index'].min()} to {df_feat.loc[test_mask, 'week_index'].max()} (N={test_mask.sum()})")
    
    unique_vegs = df_feat["product_name"].unique()
    cal_scores = []
    test_scores = []
    
    for veg in unique_vegs:
        v_df = df_feat[df_feat["product_name"] == veg].sort_values("week_index")
        prices = v_df["price_lkr"].values
        cat = v_df["category"].iloc[0]
        
        # Fit AutoARIMA on train
        tr_prices = v_df.loc[train_mask.loc[v_df.index], "price_lkr"].values
        forecaster = AutoARIMARollingForecaster(d=1)
        forecaster.fit_parameters(tr_prices)
        
        # Predict val_cal
        cal_indices = [v_df.index.get_loc(idx) for idx in v_df.index[val_cal_mask.loc[v_df.index]]]
        cal_fc = forecaster.rolling_forecast(prices, cal_indices, horizon=h)
        for pos, fc in cal_fc.items():
            actual_target = v_df.iloc[pos][target_col]
            if pd.notna(actual_target) and actual_target > 0 and fc > 0:
                score = abs(np.log(actual_target) - np.log(fc))
                cal_scores.append({
                    "vegetable": veg,
                    "category": cat,
                    "week_index": v_df.iloc[pos]["week_index"],
                    "y_true": actual_target,
                    "y_pred": fc,
                    "score": score
                })
                
        # Predict test
        test_indices = [v_df.index.get_loc(idx) for idx in v_df.index[test_mask.loc[v_df.index]]]
        test_fc = forecaster.rolling_forecast(prices, test_indices, horizon=h)
        for pos, fc in test_fc.items():
            actual_target = v_df.iloc[pos][target_col]
            if pd.notna(actual_target) and actual_target > 0 and fc > 0:
                score = abs(np.log(actual_target) - np.log(fc))
                test_scores.append({
                    "vegetable": veg,
                    "category": cat,
                    "week_index": v_df.iloc[pos]["week_index"],
                    "y_true": actual_target,
                    "y_pred": fc,
                    "score": score
                })
    
    df_cal = pd.DataFrame(cal_scores)
    df_test = pd.DataFrame(test_scores)
    
    # Compute Conformal Quantiles per category (alpha=0.20 for 80% coverage)
    cat_quantiles = {}
    alpha = 0.20
    for cat in df_cal["category"].unique():
        c_scores = df_cal[df_cal["category"] == cat]["score"].values
        n = len(c_scores)
        level = min(0.999, np.ceil((n + 1) * (1.0 - alpha)) / n)
        q = np.quantile(c_scores, q=level)
        cat_quantiles[cat] = float(q)
        print(f"Category '{cat}' (N_cal={n}): q_80 = {q:.4f}, Mult Width = [x{np.exp(-q):.3f}, x{np.exp(q):.3f}], Width % = {(np.exp(q)-np.exp(-q))*100:.1f}%")
        
    cat_stats = {}
    for cat in df_cal["category"].unique():
        q = cat_quantiles[cat]
        sub_c = df_cal[df_cal["category"] == cat]
        cov_cal = ((sub_c["y_true"] >= sub_c["y_pred"] * np.exp(-q)) & (sub_c["y_true"] <= sub_c["y_pred"] * np.exp(q))).mean() * 100.0
        sub_t = df_test[df_test["category"] == cat]
        cov_test = ((sub_t["y_true"] >= sub_t["y_pred"] * np.exp(-q)) & (sub_t["y_true"] <= sub_t["y_pred"] * np.exp(q))).mean() * 100.0
        rel_width = (np.exp(q) - np.exp(-q)) * 100.0
        cat_stats[cat] = {
            "q_80": q,
            "cov_cal": cov_cal,
            "cov_test": cov_test,
            "rel_width": rel_width
        }
        
    veg_stats = {}
    for veg in unique_vegs:
        cat = df_feat[df_feat["product_name"] == veg]["category"].iloc[0]
        q = cat_quantiles[cat]
        sub_c = df_cal[df_cal["vegetable"] == veg]
        cov_cal = ((sub_c["y_true"] >= sub_c["y_pred"] * np.exp(-q)) & (sub_c["y_true"] <= sub_c["y_pred"] * np.exp(q))).mean() * 100.0
        sub_t = df_test[df_test["vegetable"] == veg]
        cov_test = ((sub_t["y_true"] >= sub_t["y_pred"] * np.exp(-q)) & (sub_t["y_true"] <= sub_t["y_pred"] * np.exp(q))).mean() * 100.0
        veg_stats[veg] = {
            "cov_cal": cov_cal,
            "cov_test": cov_test,
            "rel_width": (np.exp(q) - np.exp(-q)) * 100.0
        }
        
    # Forward Forecast: Origin = Week 464 (2026-08-25), Target = Week 468 (h=4)
    origin_week = 464
    target_week = 468
    latest_origin_date = df_feat[df_feat["week_index"] == origin_week]["approx_date"].iloc[0]
    
    # FIXED HYPOTHETICAL SYNTHETIC COSTS (completely decoupled from forecast and origin price)
    fixed_synthetic_costs = {
        # Upcountry (Rs/kg)
        "Beans Butter": 420.0,
        "Beans Green": 340.0,
        "Beet Root": 220.0,
        "Cabbage Seed": 150.0,
        "Carrot": 290.0,
        "Knolkhol": 180.0,
        "Leeks": 230.0,
        "Raddish": 120.0,
        # Leafy (Rs/bundle)
        "Gotukola": 25.0,
        "Mukunuwenna": 22.0,
        "Kankun": 24.0,
        "Spinach": 35.0,
        "Sarana": 20.0,
        "Thampala": 22.0,
        "Mint": 30.0,
        "Murunga leaves": 28.0,
        # Lowland (Rs/kg)
        "Ash Plantain": 140.0,
        "Ash Pumpkin": 180.0,
        "Bandakka": 190.0,
        "Bitter Gourd": 240.0,
        "Brinjal": 210.0,
        "Capsicum": 380.0,
        "Cucumber": 110.0,
        "Drumstick": 650.0,
        "Ginger": 550.0,
        "Green Chillies": 480.0,
        "Lime": 320.0,
        "Luffa": 160.0,
        "Red Pumpkin": 95.0,
        "Snake Gourd": 150.0,
        "Tomato No1.": 220.0,
        "Winged Bean": 230.0
    }
    
    forward_records = []
    
    for veg in unique_vegs:
        v_df = df_feat[df_feat["product_name"] == veg].sort_values("week_index")
        prices = v_df["price_lkr"].values
        cat = v_df["category"].iloc[0]
        unit = v_df["unit"].iloc[0]
        orig_p = prices[-1] # week 464 price
        
        # Fit AutoARIMA on ALL 464 weeks
        forecaster = AutoARIMARollingForecaster(d=1)
        forecaster.fit_parameters(prices)
        fc_dict = forecaster.rolling_forecast(prices, [len(prices)-1], horizon=h)
        fc_p = fc_dict.get(len(prices)-1, float(prices[-1]))
        fc_p = max(0.0, float(fc_p))
        
        fc_to_price_ratio = fc_p / orig_p if orig_p > 0 else 1.0
        
        q = cat_quantiles[cat]
        lower_80 = fc_p * np.exp(-q)
        upper_80 = fc_p * np.exp(q)
        rel_w = (np.exp(q) - np.exp(-q)) * 100.0
        
        cost = fixed_synthetic_costs.get(veg, 150.0)
        net_margin = round(fc_p - cost, 2)
        margin_pct = round((net_margin / cost) * 100.0, 1)
        
        v_cov_test = veg_stats[veg]["cov_test"]
        v_cov_cal = veg_stats[veg]["cov_cal"]
        
        if net_margin > 0:
            if lower_80 > cost:
                risk = f"Viable (Lower 80% CI > Cost, Rel Width {rel_w:.1f}%)"
            else:
                risk = f"Downside Risk (Lower 80% CI <= Cost, Rel Width {rel_w:.1f}%)"
        else:
            risk = f"Negative Margin (Expected Loss, Rel Width {rel_w:.1f}%)"
            
        forward_records.append({
            "vegetable": veg,
            "category": cat,
            "unit": unit,
            "price_at_week_464": round(orig_p, 2),
            "forecast_price_lkr": round(fc_p, 2),
            "forecast_to_price_ratio": round(fc_to_price_ratio, 3),
            "synthetic_cost_lkr": round(cost, 2),
            "lower_80_lkr": round(lower_80, 2),
            "upper_80_lkr": round(upper_80, 2),
            "multiplier_lower": round(float(np.exp(-q)), 3),
            "multiplier_upper": round(float(np.exp(q)), 3),
            "relative_width_pct": round(rel_w, 1),
            "empirical_test_coverage": f"{v_cov_test:.1f}%",
            "empirical_cal_coverage": f"{v_cov_cal:.1f}%",
            "category_test_coverage": f"{cat_stats[cat]['cov_test']:.1f}%",
            "net_margin_lkr": net_margin,
            "margin_pct": margin_pct,
            "risk_classification": risk
        })
        
    df_sec9 = pd.DataFrame(forward_records)
    out_csv = Path("results/tables/section9_decision_support.csv")
    df_sec9.to_csv(out_csv, index=False)
    print(f"\nSaved updated forward forecast to {out_csv} (32 vegetables)")
    return df_sec9

if __name__ == "__main__":
    run_forward_forecast()
