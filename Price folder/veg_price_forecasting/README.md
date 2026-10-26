# Sri Lankan Market Vegetable Price Forecasting Pipeline

A research-grade, reproducible, multi-horizon time-series forecasting framework designed to predict weekly market prices of vegetables in Sri Lanka (2017–2026), quantify forecast uncertainty via conformal prediction, and estimate farmer profit margins against crop production costs for thesis research.

---

## 1. Research Context & Purpose
In agricultural economics and decision-support systems for smallholder farmers, harvest planning requires reliable forecasts of future market prices weeks to months ahead of harvest. 
- **Cost Model Integration**: This market price prediction module produces expected market prices ($\hat{y}_{t+h}$) and 80%/95% prediction intervals $[L_{t+h}, U_{t+h}]$.
- **Profit Margin Estimation**: Predictions are joined with crop cultivation cost models to compute farmer profit margins:
  $$\text{Expected Margin} = \hat{y}_{t+h} - \text{Production Cost}$$
  $$\text{Risk-Adjusted Margin (80\% Lower Bound)} = L_{t+h} - \text{Production Cost}$$

---

## 2. Directory & Project Structure
```
Price folder/
├── raw_bulletins/               # Primary archive of raw Excel price bulletins (2017–2026)
│   ├── 2017/ ... 2026/
├── etl/                         # Master dataset ingestion & cleaning pipeline
│   ├── build_master.py          # Multi-year Excel parsing & normalization engine
│   └── _output/                 # Emitted master CSVs, revisions, and layout reports
└── veg_price_forecasting/       # Production research & forecasting repository
    ├── pyproject.toml           # Package configuration & editable installation
    ├── config.yaml              # Global paths, splits, horizons, Optuna trial budgets & seeds
    ├── requirements.txt         # Locked Python dependencies
    ├── run_pipeline.py          # End-to-end experiment pipeline orchestrator (--smoke-test / --full)
    ├── freeze_models.py         # Production model serialization & SHA-256 manifest builder
    ├── score_holdout.py         # Holdout test set scoring & verification tool
    ├── backend/                 # FastAPI REST inference service
    │   ├── main.py              # Endpoints (/vegetables, /history, /forecast) with CORS
    │   └── inference.py         # Causal inference engine with disk cache
    ├── frontend/                # React + Vite + Tailwind interactive web app
    │   ├── src/App.jsx          # Commodity selector, Recharts trajectory fan & benchmark tables
    │   └── tailwind.config.js
    ├── src/                     # Core research Python package
    │   ├── data.py              # SHA-256 verifier, spelling fixes, stale-run detector
    │   ├── splits.py            # Expanding-window time-series CV generator (gap >= h)
    │   ├── features.py          # Causal lags, rolling statistics, cross-veg category means
    │   ├── metrics.py           # MAE, RMSE, MAPE, sMAPE, MASE, R2, DM-test, Friedman test
    │   ├── intervals.py         # Scale-aware split-conformal prediction calibrator
    │   ├── utils.py             # Deterministic seed management, run ID generation
    │   ├── models/              # Baselines, Statistical (ETS/ARIMA), Classical ML, DL, Ensembles
    │   ├── train.py             # Walk-forward CV tuning, model fitting, and leaderboard builder
    │   └── evaluate.py          # Thesis figures (PNG/SVG) and LaTeX/CSV comparison tables
    ├── scripts/                 # Modular research, diagnostic & reporting scripts
    │   ├── experiments/         # Ablation, placebo, and purged pipeline experiment scripts
    │   ├── audits/              # Data integrity, split verification, and diagnostic audits
    │   ├── reporting/           # Report table generators & HTML documentation renderers
    │   └── scratch/             # Exploratory research & scratchpad investigation scripts
    ├── tests/                   # Verification and unit tests
    ├── models/
    │   ├── frozen/              # SHA-256 frozen winning models (Lasso, AutoARIMA, CatBoost, Transformer)
    │   └── best_model/          # Model artifact (model.joblib) + MODEL_CARD.md
    ├── experiments/
    │   ├── leaderboard.csv      # Unified leaderboard across all models, horizons & splits
    │   ├── leaderboard_by_vegetable.csv # Disaggregated metrics per vegetable variety
    │   └── runs/                # Checkpointed runs with config.json, metrics.json, prediction CSVs
    ├── results/
    │   ├── figures/             # Publication figures (Heatmaps, Degradation curves, Intervals)
    │   ├── tables/              # Publication LaTeX and CSV tables for thesis
    │   └── report.md / report.html # Comprehensive analytical research report
    ├── notebooks/               # 10 Executed, Colab-compatible notebooks (.ipynb and .html)
    └── inference/               # CLI inference tool & profit margin estimator
```

---

## 3. Pre-Fixed Model Selection Rule
To eliminate p-hacking and prevent test-set data snooping, the model selection protocol was strictly established before training:
1. **Primary Evaluation Metric**: Lowest **median MASE** (Mean Absolute Scaled Error) across all vegetables.
2. **Evaluation Split**: Evaluated exclusively on the **VALIDATION** period (2024-09 to 2025-08, 48 reporting weeks).
3. **Primary Forecast Horizon**: $h = 4$ weeks ahead (standard agricultural planning horizon).
4. **Tie-Breakers**:
   - First: Lowest symmetric Mean Absolute Percentage Error (**sMAPE**).
   - Second: Highest empirical coverage rate on the nominal **80% Prediction Interval**.
5. **Deployment Protocol**: The winning model on validation is evaluated once on the out-of-sample **TEST** split (2025-09 to 2026-08), refit on ALL historical data (Train + Val + Test), and serialized to `models/best_model/model.joblib`.

---

## 4. Strict Leakage Prevention & Calendar Structure
1. **The 48-Week Reporting Calendar**:
   The reporting calendar in the source weekly Excel price bulletins structures each month into exactly 4 reporting weeks (Week 1 to Week 4), yielding exactly 48 reporting weeks per year ($4 \times 12 = 48$). Consequently, the annual seasonal lag is strictly lag 48 (representing the identical reporting week in the prior calendar year), rather than standard 52 calendar weeks.
2. **Chronological Partitioning**:
   - **TRAIN**: 2017-01-04 to 2024-08-25 (Weeks 1 to 368, ~7.7 years, 11,776 observations).
   - **VALIDATION**: 2024-09-04 to 2025-08-25 (Weeks 369 to 416, 48 weekly reporting periods, 1.0 year):
     - **Val-Tune**: Weeks 369 to 392 (768 obs) for hyperparameter tuning and model evaluation.
     - **Val-Cal**: Weeks 393 to 416 (768 obs) strictly held out for conformal interval calibration.
   - **TEST**: 2025-09-04 to 2026-08-25 (Weeks 417 to 464, 48 weekly reporting periods, 1.0 year, 1,536 observations).
3. **Walk-Forward CV with Blackout Gap**: Hyperparameters are tuned strictly on the training set using an expanding-window scheme with a blackout gap $\ge h$ weeks to eliminate lookahead leakage.
4. **Causal Missing Value Handling**: Missing inputs are handled via strictly forward-fill (maximum 2 consecutive weeks) coupled with a binary missingness indicator. No future or backward interpolation is ever used.
5. **Leak-Free Preprocessing**: Feature scalers, target scalers, and categorical encoders are fit exclusively on historical training partitions.

---

## 5. Model Suite Overview
The pipeline benchmarks **31 models across 5 distinct modeling paradigms**:
1. **Baselines (5)**: Naive (persistence $y_t$), Seasonal Naive (48-week lag), Moving Average (4-week, 12-week), Drift.
2. **Local Statistical Models (4)**: Holt-Winters Exponential Smoothing (damped additive trend, log scale), Auto-ARIMA (Kalman update via `apply`), SARIMAX (with category signals), and Prophet with autoregressive residual state updates (all evaluated via strict rolling-origin forecasting).
3. **Global Classical Machine Learning (11)**: Linear Regression, Ridge, Lasso, ElasticNet, Support Vector Regression (SVR with StandardScaler pipeline), Random Forest, Extra Trees, Gradient Boosting Regressor, LightGBM, XGBoost, CatBoost.
4. **Global Deep Learning in PyTorch (8)**: Multi-Layer Perceptron (MLP), Long Short-Term Memory (LSTM), Gated Recurrent Unit (GRU), 1D Temporal Convolutional Network (TCN), N-BEATS Basis Expansion Block Network, Self-Attention Transformer Forecaster, N-HiTS (Neural Hierarchical Interpolation with multi-rate pooling), and Temporal Fusion Transformer (TFT-Lite).
5. **Ensembles (3)**: Simple Average Top-3 Ensemble, Stacking Meta-Learner (constrained non-negative Ridge fitted on validation out-of-fold predictions), and Best-Per-Category Selection.

---

## 6. How to Run

### Installation
```bash
python -m pip install -r requirements.txt
```

### 1. Run Rapid Smoke Test
Evaluates 3 representative vegetables (`Carrot`, `Green Chillies`, `Drumstick`) across 2 horizons ($h=1, 4$):
```bash
python run_pipeline.py --smoke-test
```

### 2. Run Full Research Benchmark
Executes all 32 vegetable varieties across all 4 forecast horizons ($h=1, 4, 8, 12$):
```bash
python run_pipeline.py
```

### 3. Generate & Execute All 10 Colab Notebooks
```bash
python build_all_notebooks.py
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb
python -m jupyter nbconvert --to html notebooks/*.ipynb
```

### 4. Interactive CLI Inference
Generate expected prices and 80%/95% confidence bounds:
```bash
python inference/predict.py --vegetable Carrot --date 2026-08-25 --horizon 4
```

### 5. Compute Farmer Profit Margins
```bash
python inference/profit_margin_example.py
```

---

## 7. Results Summary (Primary Horizon $h=4$ Weeks)

| Model Family | Model Architecture | Validation MASE | Validation sMAPE (%) | Test MASE | Test sMAPE (%) | Test 80% Coverage | Test 95% Coverage |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Ensemble** | **Simple Average Top-3** | **1.2360** | **26.60%** | **0.9674** | **26.52%** | **83.5%** | **95.3%** |
| Classical ML | Lasso Regressor | 1.2607 | 28.24% | 0.9682 | 26.56% | 81.1% | 95.3% |
| Classical ML | XGBoost | 1.2696 | 26.70% | 1.0559 | 27.74% | 81.1% | 92.9% |
| Deep Learning | 1D TCN (Dilated ConvNet) | 1.2803 | 27.77% | 0.9537 | 26.46% | 81.9% | 95.3% |
| Deep Learning | N-BEATS | 1.3095 | 28.49% | 0.9592 | 26.42% | 82.7% | 94.5% |
| Classical ML | Gradient Boosting | 1.3378 | 28.09% | 1.0007 | 26.44% | 83.5% | 93.7% |
| Classical ML | CatBoost | 1.3436 | 28.44% | 1.0028 | 26.31% | 85.0% | 98.4% |
| Baseline | Naive (Persistence) | 1.6275 | 35.60% | 1.1670 | 31.19% | 77.2% | 96.1% |
| Baseline | Seasonal Naive (48-wk) | 1.7570 | 41.22% | 1.4445 | 37.12% | 78.0% | 97.6% |
| Statistical | Holt-Winters ETS | 2.5875 | 68.47% | 1.5271 | 47.17% | 92.1% | 100.0% |

**Winning Model**: `simple_average_top3` (combining Lasso, XGBoost, and 1D TCN).
- Achieves lowest Validation MASE of **1.2360** and Test MASE of **0.9674** (outperforming seasonal persistence by >33%).
- Calibrated conformal prediction intervals achieve **83.5% empirical coverage** for nominal 80% and **95.3% empirical coverage** for nominal 95%.
