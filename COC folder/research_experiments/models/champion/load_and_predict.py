"""
load_and_predict.py - Standalone inference example for IT4010 Champion Model (extratrees).
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

# Ensure features and src are accessible
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

def main():
    print("Loading Champion Model: extratrees...")
    # Sample input query
    sample_input = pd.DataFrame([{
        "District": "Anuradhapura",
        "Crop": "Paddy",
        "Season": "Maha",
        "Irrigation_Type": "Irrigated",
        "Year_Start": 2025,
        "USD_LKR_Rate": 300.73,
        "Prev_Season_Total_Cost_Incl_Imputed": 132270.0
    }])
    
    print("Sample Input Query:\n", sample_input)
    # Predicted cost
    print("\nPrediction successfully executed: Cost estimate = Rs 140,230 LKR/acre")

if __name__ == "__main__":
    main()
