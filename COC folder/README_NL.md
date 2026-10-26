# LLM-Powered Natural Language Interface for SO1 Cost Prediction

This module provides a natural language query interface for the Sri Lanka Agricultural Cost of Cultivation (COC) Predictive Engine using the locally-hosted Ollama model **`llama3.1:8b`**.

---

## 1. Architecture Overview

```
User Query (e.g., "What will it cost to grow tomato in Hambantota this Yala on 1.5 acres?")
       │
       ▼
1. parse_query (Ollama llama3.1:8b, format='json')
   - Extracts: district, crop, season, irrigation_type, field_size_acres, prev_season_cost
       │
       ▼
2. Calibrated Prediction Pipeline (FastAPI /predict or predict_with_intervals.py)
   - Evaluates: GradientBoostingRegressor + SHAP feature attributions + log-residual intervals
       │
       ▼
3. generate_narrative (Ollama llama3.1:8b)
   - Plain-language explanation for farmers & agricultural extension officers
   - Predicted cost, expected 80% range, top cost drivers, confidence flag, action advice
       │
       ▼
Officer Assistant Response & Interactive Collapsible Structured Data Table
```

---

## 2. Prerequisites & Installation

### A. Install Ollama
Download and install Ollama for Windows/macOS/Linux:
- **Download link**: [https://ollama.com/download](https://ollama.com/download)

### B. Pull the Llama 3.1 8B Model
Open PowerShell or your terminal and pull the model:
```bash
ollama pull llama3.1:8b
```
*(Model size: ~4.7 GB. Runs locally on CPU or GPU with zero cloud token costs).*

### C. Verify Ollama is Running
Ollama typically auto-runs as a background service. Verify via HTTP:
```bash
curl http://localhost:11434/api/tags
```
Expected output includes `"name": "llama3.1:8b"`.

If Ollama is not running, start it manually:
```bash
ollama serve
```

### D. Install Python Packages
```bash
pip install ollama langchain langchain-community
```

---

## 3. Running and Testing

### A. Run Automated Natural Language Test Suite
To evaluate the 3 benchmark test queries and output results to `nl_test_outputs.txt`:
```bash
python test_nl.py
```

### B. Start the Full Backend & Frontend Services
1. **Start the FastAPI backend**:
   ```bash
   uvicorn prediction_api:app --host 0.0.0.0 --port 8000 --reload
   ```
2. **Start the React + Vite frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
3. Navigate to **http://localhost:5173/chat** to interact with the conversational AI assistant.

---

## 4. API Specification: `POST /chat`

### Request Body
```json
{
  "message": "What will it cost to grow tomato in Hambantota this Yala on 1.5 acres?"
}
```

### Response Body
```json
{
  "request_id": "848e42db-2ec7-4ca4-bb3f-561b369da8ef",
  "timestamp": "2026-09-25T16:47:40.011Z",
  "parsed_input": {
    "district": "Hambantota",
    "crop": "Tomato",
    "season": "Yala",
    "irrigation_type": "Unspecified",
    "field_size_acres": 1.5,
    "prev_season_cost": null,
    "season_inferred": false
  },
  "prediction": {
    "predicted_cost": 449919.1,
    "interval_low": 361468.0,
    "interval_high": 560014.0,
    "low_confidence": false,
    "low_confidence_reason": null,
    "reference_note": "Model reference year is 2025 (latest available data).",
    "top_drivers": [
      {"feature": "Prev_Season_Total_Cost_Incl_Imputed", "contribution_pct": 50.6, "direction": "+"},
      {"feature": "Year_Start", "contribution_pct": 17.8, "direction": "+"},
      {"feature": "Crop", "contribution_pct": 15.7, "direction": "+"}
    ],
    "model_version": "gb_tuned_v1"
  },
  "narrative": "The predicted cost to grow tomato in Hambantota this Yala season is Rs 449,919 LKR per acre. We are 80% confident that the actual cost will be between Rs 361,468 to Rs 560,014 LKR per acre...",
  "model_version": "gb_tuned_v1"
}
```

### HTTP Error Codes:
- `HTTP 422 Unprocessable Entity`: Triggered if the query does not contain a recognizable crop or district. Includes suggestions to rephrase.
- `HTTP 503 Service Unavailable`: Triggered if Ollama is not running or unreachable:
  `"LLM service unavailable. Ensure Ollama is running: ollama serve"`

---

## 5. Troubleshooting & FAQ

1. **Slow First Response (Warmup Latency)**:
   - On CPU, the initial prompt takes ~15–25 seconds while model weights are loaded into system memory.
   - Subsequent responses typically take **2–5 seconds**, which is optimal for field officers.
2. **Error: `LLM service unavailable`**:
   - Ensure the Ollama icon is visible in the system tray or run `ollama serve` in a terminal.
   - Test connectivity with `curl http://localhost:11434/api/tags`.
3. **Model not loaded or model not found error**:
   - Run `ollama list`. If `llama3.1:8b` is missing, run `ollama pull llama3.1:8b`.
