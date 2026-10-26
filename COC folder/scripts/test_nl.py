#!/usr/bin/env python3
"""
Test Suite for Natural Language Query Interface (SO1)
=====================================================
Tests the 3 user queries using Ollama llama3.1:8b:
1. "What will it cost to grow tomato in Hambantota this Yala on 1.5 acres?"
2. "I'm advising a farmer in Nuwara Eliya about potato for next season. Is it a good time to plant?"
3. "Predict the cost for green chilli in Anuradhapura"

Prints both parsed input and generated narrative, and saves all outputs to nl_test_outputs.txt.
"""

import sys
import json
import time
from pathlib import Path

# Add current workspace to path
WORKSPACE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE))

from nl_interface import answer_officer_query, check_ollama_available

TEST_QUERIES = [
    "What will it cost to grow tomato in Hambantota this Yala on 1.5 acres?",
    "I'm advising a farmer in Nuwara Eliya about potato for next season. Is it a good time to plant?",
    "Predict the cost for green chilli in Anuradhapura"
]

OUTPUT_FILE = (WORKSPACE / "reports" / "nl_test_outputs.txt") if (WORKSPACE / "reports").exists() else (WORKSPACE / "nl_test_outputs.txt")


def run_tests():
    print("=" * 80)
    print("NATURAL LANGUAGE INTERFACE TEST SUITE (Ollama llama3.1:8b)")
    print("=" * 80)

    if not check_ollama_available():
        print("ERROR: Ollama is not running on http://localhost:11434.")
        print("Please start Ollama with 'ollama serve' before running tests.")
        sys.exit(1)

    print(f"Testing {len(TEST_QUERIES)} target queries...\n")
    
    output_lines = []
    output_lines.append("=" * 80)
    output_lines.append("SO1 NATURAL LANGUAGE QUERY BENCHMARK OUTPUTS")
    output_lines.append("Model: Ollama llama3.1:8b | Predictive Model: GradientBoostingRegressor (calibrated)")
    output_lines.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    output_lines.append("=" * 80)
    output_lines.append("")

    for idx, query in enumerate(TEST_QUERIES, 1):
        print(f"\n--- [Test Query {idx}/{len(TEST_QUERIES)}] ---")
        print(f"Query: \"{query}\"")
        t0 = time.perf_counter()

        try:
            result = answer_officer_query(query)
            elapsed = time.perf_counter() - t0

            parsed = result["parsed"]
            prediction = result["prediction"]
            narrative = result["narrative"]

            pred_cost = prediction.get("predicted_cost", 0.0)
            low = prediction.get("interval_low", 0.0)
            high = prediction.get("interval_high", 0.0)
            low_conf = prediction.get("low_confidence", False)

            print(f"Parsed Input:\n{json.dumps(parsed, indent=2)}")
            print(f"Prediction: Rs {pred_cost:,.1f} [Rs {low:,.1f} - Rs {high:,.1f}] (Low Conf: {low_conf})")
            print(f"Narrative:\n{narrative}")
            print(f"Elapsed: {elapsed:.2f}s")

            # Append to file report
            output_lines.append(f"TEST QUERY {idx}:")
            output_lines.append(f"Query: \"{query}\"")
            output_lines.append(f"Response Time: {elapsed:.2f} seconds")
            output_lines.append("")
            output_lines.append("PARSED INPUT (JSON):")
            output_lines.append(json.dumps(parsed, indent=2))
            output_lines.append("")
            output_lines.append("PREDICTION METRICS:")
            output_lines.append(f"  - Predicted Cost : Rs {pred_cost:,.1f} per acre")
            output_lines.append(f"  - 80% Range      : Rs {low:,.1f} to Rs {high:,.1f} per acre")
            output_lines.append(f"  - Low Confidence : {low_conf}")
            if prediction.get("warning"):
                output_lines.append(f"  - Warning        : {prediction.get('warning')}")
            if parsed.get("field_size_acres"):
                total_cost = pred_cost * parsed["field_size_acres"]
                output_lines.append(f"  - Field Size     : {parsed['field_size_acres']} acres (Total: Rs {total_cost:,.1f})")
            output_lines.append("")
            output_lines.append("GENERATED NARRATIVE:")
            output_lines.append(narrative)
            output_lines.append("")
            output_lines.append("-" * 80)
            output_lines.append("")

        except Exception as e:
            print(f"ERROR on query {idx}: {e}")
            output_lines.append(f"TEST QUERY {idx} (ERROR):")
            output_lines.append(f"Query: \"{query}\"")
            output_lines.append(f"Error: {str(e)}")
            output_lines.append("")
            output_lines.append("-" * 80)
            output_lines.append("")

    # Save to nl_test_outputs.txt
    OUTPUT_FILE.write_text("\n".join(output_lines), encoding="utf-8")
    print(f"\n[Success] All test outputs written to {OUTPUT_FILE.name}")


if __name__ == "__main__":
    run_tests()
