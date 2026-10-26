"""
models_llm.py - General LLM in-context / few-shot text regression benchmark via local Ollama.
Guarantees zero-leakage prompt construction, temperature 0 deterministic inference, and transparent failure logging.
"""

import re
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
import ollama


def extract_numeric_cost(text: str) -> Optional[float]:
    """
    Deterministically parses numeric currency / cost value from LLM completion.
    Handles 'Rs', 'LKR', commas, and decimals.
    """
    cleaned = text.replace(",", "").strip()

    # Pattern: match explicit numbers (e.g. "Rs 150000", "150,000", "150000.50")
    matches = re.findall(r"(?:Rs\.?|LKR)?\s*([0-9]+(?:\.[0-9]+)?)", cleaned, re.IGNORECASE)
    if matches:
        for m in matches:
            val = float(m)
            # Agricultural cost sanity bounds: Rs 10,000 to Rs 2,500,000 per acre
            if 10000.0 <= val <= 2500000.0:
                return val
        # If no number inside bounds, return the first valid float
        return float(matches[0])
    return None


class OllamaLLMBenchmark:
    """
    Few-Shot In-Context Regression Benchmark using local Ollama (LLaMA-3.1 8B).
    """
    def __init__(self, model_name: str = "llama3.1:8b", k_shot: int = 3, timeout_seconds: int = 30):
        self.model_name = model_name
        self.k_shot = k_shot
        self.timeout_seconds = timeout_seconds
        self.prompt_logs_ = []
        self.parse_failures_ = []

    def _build_prompt(self, target_row: pd.Series, df_train: pd.DataFrame) -> str:
        """
        Builds in-context prompt using k-shot examples strictly from training fold.
        Selects examples from same crop and most recent years available in training data.
        """
        crop = target_row["Crop"]
        candidates = df_train[df_train["Crop"] == crop]
        if len(candidates) < self.k_shot:
            candidates = df_train

        # Sort by latest available training year to provide relevant context
        examples = candidates.sort_values(by="Year_Start", ascending=False).head(self.k_shot)

        shots_text = ""
        for _, ex in examples.iterrows():
            prev_cost_str = f"Rs {ex['Prev_Season_Total_Cost_Incl_Imputed']:,.0f}" if pd.notna(ex['Prev_Season_Total_Cost_Incl_Imputed']) else "Not Available"
            shots_text += (
                f"- District: {ex['District']}, Crop: {ex['Crop']}, Season: {ex['Season']}, "
                f"Irrigation: {ex['Irrigation_Type']}, Year: {ex['Year_Start']}, "
                f"USD/LKR Rate: {ex['USD_LKR_Rate']}, Prior Season Cost: {prev_cost_str} "
                f"-> Total Cost: Rs {ex['Total_Cost_Incl_Imputed']:,.0f} LKR/acre\n"
            )

        target_prev_cost_str = (
            f"Rs {target_row['Prev_Season_Total_Cost_Incl_Imputed']:,.0f}"
            if pd.notna(target_row["Prev_Season_Total_Cost_Incl_Imputed"])
            else "Not Available"
        )

        prompt = f"""You are an agricultural economist predicting crop cultivation expenditure in Sri Lanka.
Predict the Total Cultivation Cost Including Imputed Cost (in LKR per acre) for the target farm based on macroeconomic conditions and prior season history.

### Historical Benchmarks (from previous verified surveys):
{shots_text}
### Target Farm Query:
- District: {target_row['District']}
- Crop: {target_row['Crop']}
- Season: {target_row['Season']}
- Irrigation Type: {target_row['Irrigation_Type']}
- Cultivation Year: {target_row['Year_Start']}
- CBSL USD/LKR Rate: {target_row['USD_LKR_Rate']}
- Previous Season Total Cost: {target_prev_cost_str}

Provide ONLY the predicted numeric cost in LKR/acre. Do not include any explanations.
Predicted Cost (LKR/acre):"""
        return prompt

    def predict_row(self, target_row: pd.Series, df_train: pd.DataFrame) -> Tuple[float, bool]:
        """Queries Ollama for a single row prediction."""
        prompt = self._build_prompt(target_row, df_train)
        start_time = time.time()
        raw_response = ""
        predicted_cost = None
        parse_success = False

        try:
            res = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.0, "num_predict": 25}
            )
            raw_response = res["message"]["content"].strip()
            parsed = extract_numeric_cost(raw_response)
            if parsed is not None:
                predicted_cost = parsed
                parse_success = True
            else:
                self.parse_failures_.append({
                    "row_id": target_row.get("row_id", -1),
                    "raw_response": raw_response,
                    "reason": "regex_extraction_failed"
                })
        except Exception as e:
            self.parse_failures_.append({
                "row_id": target_row.get("row_id", -1),
                "raw_response": str(e),
                "reason": "ollama_call_error"
            })

        latency = time.time() - start_time

        # Fallback to crop training median if LLM call or parse fails
        if predicted_cost is None:
            crop_median = df_train[df_train["Crop"] == target_row["Crop"]]["Total_Cost_Incl_Imputed"].median()
            predicted_cost = float(crop_median) if pd.notna(crop_median) else 100000.0

        self.prompt_logs_.append({
            "target_crop": target_row["Crop"],
            "target_year": int(target_row["Year_Start"]),
            "prompt": prompt,
            "raw_response": raw_response,
            "parsed_cost": predicted_cost,
            "parse_success": parse_success,
            "latency_seconds": round(latency, 2)
        })

        return predicted_cost, parse_success

    def save_logs(self, log_dir: Path):
        """Saves prompt audit log and failure report."""
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "llm_prompts_and_raw_responses.jsonl"
        with open(log_path, "w", encoding="utf-8") as f:
            for item in self.prompt_logs_:
                f.write(json.dumps(item) + "\n")

        if self.parse_failures_:
            pd.DataFrame(self.parse_failures_).to_csv(log_dir / "llm_failures.csv", index=False)
