#!/usr/bin/env python3
"""
Add Exchange Rate and USD-Adjusted Cost to COC Master Dataset
=============================================================
This script:
1. Reads coc_master.csv.
2. Ensures Year_Start integer column is properly set/derived.
3. Merges the annual average LKR/USD exchange rate table.
4. Computes Total_Cost_Incl_Imputed_USD = Total_Cost_Incl_Imputed / USD_LKR_Rate.
5. Saves the augmented dataset as coc_master_v2.csv.
6. Prints null counts and summaries of the new fields.
7. Produces a dual-panel matplotlib chart (exchange_rate_check.png)
   comparing raw LKR costs vs USD-adjusted costs over time.
"""

import sys
import re
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def main():
    print("=" * 80)
    print("STEP 1: Reading coc_master.csv")
    print("=" * 80)
    workspace = Path(__file__).resolve().parent.parent
    if not (workspace / "data").exists():
        workspace = Path(r"c:\Users\MSI\Desktop\Research\COC folder")
    data_dir = workspace / "data" / "processed" if (workspace / "data" / "processed").exists() else workspace
    figures_dir = workspace / "figures" if (workspace / "figures").exists() else workspace
    master_csv = data_dir / "coc_master.csv"
    if not master_csv.exists():
        print(f"Error: {master_csv} does not exist!")
        sys.exit(1)
        
    df = pd.read_csv(master_csv)
    print(f"Decision: Loaded {len(df)} rows and {len(df.columns)} columns from {master_csv.name}.")
    
    print("\n" + "=" * 80)
    print("STEP 2: Verifying and Deriving 'Year_Start'")
    print("=" * 80)
    # Check if 'Year_Start' exists or needs derivation
    if "Year_Start" in df.columns:
        print("Decision: 'Year_Start' column already exists in coc_master.csv.")
        df["Year_Start"] = df["Year_Start"].astype(int)
    elif "year" in df.columns:
        print("Decision: Using existing 'year' column as Year_Start.")
        df["Year_Start"] = df["year"].astype(int)
    else:
        print("Decision: Deriving 'Year_Start' from 'Season' and 'Year_Range'.")
        def derive_year(row):
            yr = str(row.get("Year_Range", ""))
            m = re.search(r"(\d{4})", yr)
            if m:
                return int(m.group(1))
            return np.nan
        df["Year_Start"] = df.apply(derive_year, axis=1).astype(int)

    unique_years = sorted(df["Year_Start"].unique())
    print(f"Found {len(unique_years)} distinct starting years: {unique_years}")

    print("\n" + "=" * 80)
    print("STEP 3: Merging Annual Average LKR/USD Exchange Rate Table")
    print("=" * 80)
    fx_table = {
        2014: 130.54,
        2015: 135.87,
        2016: 145.73,
        2017: 152.43,
        2018: 162.25,
        2019: 178.51,
        2020: 185.33,
        2021: 197.90,
        2022: 321.53,
        2023: 326.63,
        2024: 301.68,
        2025: 300.73,
    }
    df_fx = pd.DataFrame(list(fx_table.items()), columns=["Year_Start", "USD_LKR_Rate"])
    print("Decision: Created LKR/USD conversion table across years 2014-2025:")
    for yr, rate in fx_table.items():
        print(f"   {yr}: {rate:6.2f} LKR / USD")
        
    df = df.merge(df_fx, on="Year_Start", how="left")
    print(f"Decision: Successfully merged 'USD_LKR_Rate' column into dataset.")

    print("\n" + "=" * 80)
    print("STEP 4: Calculating 'Total_Cost_Incl_Imputed_USD'")
    print("=" * 80)
    # Check cost column naming (case insensitive check)
    target_col = None
    for col in df.columns:
        if col.lower() == "total_cost_incl_imputed":
            target_col = col
            break
            
    if not target_col:
        print("Error: Could not locate 'Total_Cost_Incl_Imputed' column!")
        sys.exit(1)
        
    print(f"Decision: Using target column '{target_col}' for USD normalization.")
    df["Total_Cost_Incl_Imputed_USD"] = df[target_col] / df["USD_LKR_Rate"]
    print("Decision: Computed Total_Cost_Incl_Imputed_USD = Total_Cost_Incl_Imputed / USD_LKR_Rate.")

    print("\n" + "=" * 80)
    print("STEP 5: Saving to coc_master_v2.csv")
    print("=" * 80)
    v2_path = data_dir / "coc_master_v2.csv"
    df.to_csv(v2_path, index=False, encoding="utf-8-sig")
    print(f"Decision: Saved augmented dataset to {v2_path} (original coc_master.csv preserved).")
    print(f"Row count: {len(df)}, Column count: {len(df.columns)}")

    print("\n" + "=" * 80)
    print("STEP 6: Null-Count & Summary for New Columns")
    print("=" * 80)
    for col in ["USD_LKR_Rate", "Total_Cost_Incl_Imputed_USD"]:
        nulls = df[col].isnull().sum()
        pct = (nulls / len(df)) * 100
        print(f"Column '{col}':")
        print(f"  - Null count : {nulls} ({pct:.2f}%)")
        print(f"  - Min value  : {df[col].min():.2f}")
        print(f"  - Mean value : {df[col].mean():.2f}")
        print(f"  - Max value  : {df[col].max():.2f}")

    print("\n" + "=" * 80)
    print("STEP 7: Generating exchange_rate_check.png")
    print("=" * 80)
    
    # Calculate yearly aggregated statistics
    grouped = df.groupby("Year_Start").agg(
        mean_lkr=(target_col, "mean"),
        std_lkr=(target_col, "std"),
        mean_usd=("Total_Cost_Incl_Imputed_USD", "mean"),
        std_usd=("Total_Cost_Incl_Imputed_USD", "std"),
        median_lkr=(target_col, "median"),
        median_usd=("Total_Cost_Incl_Imputed_USD", "median"),
        count=(target_col, "count")
    ).reset_index()
    
    print("Yearly Cost Summary by Year_Start:")
    print(grouped[["Year_Start", "count", "mean_lkr", "mean_usd"]].to_string(index=False))

    # Plot styling
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), sharex=True)
    fig.patch.set_facecolor('#f8fafc')
    
    # Panel A: Raw LKR Cost
    ax1.set_facecolor('#ffffff')
    ax1.plot(grouped["Year_Start"], grouped["mean_lkr"], marker='o', color='#dc2626', linewidth=2.5, markersize=8, label='Mean Cost (LKR)')
    ax1.fill_between(grouped["Year_Start"], 
                     grouped["mean_lkr"] - grouped["std_lkr"] * 0.25, 
                     grouped["mean_lkr"] + grouped["std_lkr"] * 0.25, 
                     color='#dc2626', alpha=0.15, label='±0.25 Std Dev')
    
    for _, r in grouped.iterrows():
        ax1.annotate(f"{r['mean_lkr']:,.0f}", 
                     (r['Year_Start'], r['mean_lkr']), 
                     textcoords="offset points", 
                     xytext=(0, 10), 
                     ha='center', 
                     fontsize=8.5, 
                     fontweight='bold', 
                     color='#991b1b')
        
    ax1.set_title("Panel A: Mean Total Cost (Raw LKR / acre)\nSpike from 2021 to 2023", fontsize=12, fontweight='bold', pad=12, color='#1e293b')
    ax1.set_xlabel("Year (Cultivation Season Start)", fontsize=10, fontweight='semibold')
    ax1.set_ylabel("Total Cost Incl. Imputed (LKR / acre)", fontsize=10, fontweight='semibold')
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.set_xticks(grouped["Year_Start"])
    ax1.set_xticklabels(grouped["Year_Start"], rotation=45)
    ax1.legend(loc='upper left', frameon=True)
    
    # Highlight 2022 devaluation shock in Panel A
    ax1.axvspan(2021.5, 2023.5, color='#fed7aa', alpha=0.3, label='Economic Crisis / Devaluation')
    
    # Panel B: USD-Adjusted Cost
    ax2.set_facecolor('#ffffff')
    ax2.plot(grouped["Year_Start"], grouped["mean_usd"], marker='s', color='#2563eb', linewidth=2.5, markersize=8, label='Mean Cost (USD)')
    ax2.fill_between(grouped["Year_Start"], 
                     grouped["mean_usd"] - grouped["std_usd"] * 0.25, 
                     grouped["mean_usd"] + grouped["std_usd"] * 0.25, 
                     color='#2563eb', alpha=0.15, label='±0.25 Std Dev')
    
    for _, r in grouped.iterrows():
        ax2.annotate(f"${r['mean_usd']:,.0f}", 
                     (r['Year_Start'], r['mean_usd']), 
                     textcoords="offset points", 
                     xytext=(0, 10), 
                     ha='center', 
                     fontsize=8.5, 
                     fontweight='bold', 
                     color='#1e40af')
        
    ax2.set_title("Panel B: Mean Total Cost (USD-Adjusted / acre)\nNormalized by Annual LKR/USD Rate", fontsize=12, fontweight='bold', pad=12, color='#1e293b')
    ax2.set_xlabel("Year (Cultivation Season Start)", fontsize=10, fontweight='semibold')
    ax2.set_ylabel("Total Cost Incl. Imputed (USD / acre)", fontsize=10, fontweight='semibold')
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.set_xticks(grouped["Year_Start"])
    ax2.set_xticklabels(grouped["Year_Start"], rotation=45)
    ax2.legend(loc='upper left', frameon=True)
    ax2.axvspan(2021.5, 2023.5, color='#fed7aa', alpha=0.3)
    
    plt.suptitle("Impact of Sri Lanka Rupee Devaluation on Agricultural Cultivation Costs (2014–2025)", 
                 fontsize=14, fontweight='bold', y=0.99, color='#0f172a')
    plt.tight_layout()
    
    fig_path = figures_dir / "exchange_rate_check.png"
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Decision: Successfully generated high-resolution chart at {fig_path}.")
    print("\n" + "=" * 80)
    print("ALL STEPS COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    main()
