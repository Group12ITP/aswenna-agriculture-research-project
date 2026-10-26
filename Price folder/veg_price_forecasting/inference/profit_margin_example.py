import pandas as pd
import numpy as np
from pathlib import Path

def compute_farmer_profit_margins():
    """
    Demonstrates research integration between market price forecasts and crop production costs.
    Computes lower, expected, and upper net margins and profit percentages.
    """
    base_dir = Path(__file__).resolve().parent
    forecast_file = base_dir / "forecast_template.csv"
    
    # 1. Load market price forecasts
    df_fc = pd.read_csv(forecast_file)
    
    # 2. SYNTHETIC EXAMPLE - NOT REAL PRODUCTION COSTS
    # The figures below are illustrative parameters for software integration demonstration only.
    # In real agricultural deployment, these figures must be ingested from the actual crop cost model CSV.
    costs_data = [
        {"vegetable": "Carrot", "unit": "1kg", "production_cost_lkr": 280.00, "cost_breakdown": "SYNTHETIC: Seeds 15%, Labor 50%, Fertilizer 25%, Transport 10%"},
        {"vegetable": "Green Chillies", "unit": "1kg", "production_cost_lkr": 420.00, "cost_breakdown": "SYNTHETIC: Harvesting Labor 55%, Inputs 30%, Transport 15%"},
        {"vegetable": "Drumstick", "unit": "1kg", "production_cost_lkr": 550.00, "cost_breakdown": "SYNTHETIC: Pruning 40%, Picking 45%, Transport 15%"},
        {"vegetable": "Leeks", "unit": "1kg", "production_cost_lkr": 210.00, "cost_breakdown": "SYNTHETIC: Fertilizer 35%, Labor 45%, Transport 20%"},
        {"vegetable": "Brinjal", "unit": "1kg", "production_cost_lkr": 160.00, "cost_breakdown": "SYNTHETIC: Pest management 35%, Labor 45%, Transport 20%"},
        {"vegetable": "Gotukola", "unit": "Bunch", "production_cost_lkr": 22.00, "cost_breakdown": "SYNTHETIC: Bed prep 30%, Weeding 50%, Transport 20%"}
    ]
    df_cost = pd.DataFrame(costs_data)
    
    # 3. Merge forecasts with production costs
    merged = df_fc.merge(df_cost, on=["vegetable", "unit"], how="inner")
    
    # 4. Compute Margins (Net Profit in Rs.cts per unit and Margin Percentage)
    # Expected Margin
    merged["margin_expected_lkr"] = merged["predicted_price_lkr"] - merged["production_cost_lkr"]
    merged["margin_expected_pct"] = (merged["margin_expected_lkr"] / merged["production_cost_lkr"]) * 100.0
    
    # Conservative 80% Lower Bound Margin (Risk Protection Threshold)
    merged["margin_lower_80_lkr"] = merged["lower_80"] - merged["production_cost_lkr"]
    merged["margin_lower_80_pct"] = (merged["margin_lower_80_lkr"] / merged["production_cost_lkr"]) * 100.0
    
    # Optimistic 80% Upper Bound Margin
    merged["margin_upper_80_lkr"] = merged["upper_80"] - merged["production_cost_lkr"]
    merged["margin_upper_80_pct"] = (merged["margin_upper_80_lkr"] / merged["production_cost_lkr"]) * 100.0
    
    # Decision / Viability Flag
    def categorize_viability(row):
        if row["margin_lower_80_lkr"] > 0:
            return "Highly Viable (Low Risk)"
        elif row["margin_expected_lkr"] > 0:
            return "Viable (Moderate Risk)"
        else:
            return "High Loss Risk"
            
    merged["farmer_recommendation"] = merged.apply(categorize_viability, axis=1)
    
    out_csv = base_dir / "profit_margin_analysis.csv"
    merged.to_csv(out_csv, index=False)
    
    print("\n" + "="*85)
    print("FARMER PROFIT MARGIN & VIABILITY ANALYSIS (HARVEST HORIZON h = 4 WEEKS)")
    print("="*85)
    cols_display = [
        "vegetable", "unit", "production_cost_lkr", "predicted_price_lkr",
        "margin_expected_lkr", "margin_expected_pct", "farmer_recommendation"
    ]
    print(merged[cols_display].to_string(index=False))
    print("="*85)
    print(f"\nDetailed analysis saved to: {out_csv}\n")
    return merged

if __name__ == "__main__":
    compute_farmer_profit_margins()
