# MODEL CARD: auto_arima (Selected Primary Horizon h=4 Forecaster)

## Model Overview
- **Model Architecture**: `auto_arima` (Univariate ARIMA with Kalman Filter Rolling Updates, $d=1$)
- **Primary Forecast Horizon**: $h=4$ weeks ahead (~1 month planning window)
- **Selection Protocol**: Pre-registered 1-SE simplicity rule on the 48-week VALIDATION period (Weeks 369 to 416).
- **Validation MASE (h=4)**: 0.7247 (falling within the 1-SE band [0.6724, 0.7305])
- **Validation sMAPE (h=4)**: 16.03%
- **Test MASE (h=4)**: 0.8517 (Test Skill vs Naive: -0.72% on full sample, +2.64% on common sample n=1400, Holm-adjusted $p=1.0000$)
- **Test sMAPE (h=4)**: 15.31%
- **Test RMSE (h=4)**: 197.46 Rs
- **80% Prediction Interval Coverage**: 80.47% (Mean Relative Width: 48.74%)
- **95% Prediction Interval Coverage**: 95.81% (Mean Relative Width: 88.58%)
- **Training Data Coverage**: Weeks 1 to 464 (2017-01-04 to 2026-08-25, 464 weekly observations per vegetable)
- **Frozen Artifact Location**: `models/frozen/selected_h4_auto_arima.joblib`
- **SHA-256 Hash**: `4ba700f01d7ec24cb1c63b7858c460d37e6daef590141f9d45e4860df890a886`

## Input Features & Inference Method
- Fits vegetable-specific $(p, 1, q)$ orders on historical log-price series via maximum likelihood (AIC minimization).
- At each forecast origin $t$, assimilates observed price innovations and projects forward $h=4$ weeks via Kalman recursion.
- Conformal prediction intervals calibrated per agro-climatic category (Leafy: 16.3% width, Lowland: 54.6% width, Upcountry: 77.2% width).
