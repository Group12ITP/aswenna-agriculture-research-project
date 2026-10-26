# Rigorous Data Leakage and Causal Integrity Audit Report

**Audit Execution Date**: 2026-10-05  
**Project**: Sri Lankan Vegetable Market Price Forecasting  
**Author**: Time-Series Quality Assurance Protocol  

---

## 1. Executive Summary & Diagnostic Scope

This audit report verifies the causal temporal structure of the vegetable price forecasting system. Rather than making unsubstantiated claims of unconditional certification, this document specifies exactly what empirical properties were verified, what was excluded from scope, and the quantified residual risks.

- **Diagnostic Test Set Invocations**: Across the research lifecycle, an exhaustive audit identified **45 Python scripts** that accessed the held-out test split (via test masks, test split labels, or test prediction evaluations) for pipeline training, diagnostic sensitivity, and statistical validation:
  1. **Primary Training Pipelines & Leaderboard Builders (4)**: `src/train.py`, `run_retrain_target_splits.py`, `run_purged_test_pipeline.py`, `run_full_leaderboard_update.py`.
  2. **Audit & Diagnostics (6)**: `src/audit_leakage.py`, `run_audit_diagnostics.py`, `run_ablation_recompute.py`, `run_ablation_exact_leaderboard.py`, `run_placebo_exact.py`, `run_interval_quality_audit.py`.
  3. **Temporal Truncation Invariance Checks (4)**: `test_all_truncation.py`, `test_all_truncation_fast.py`, `test_prophet_truncation.py`, `test_prophet_evaluated.py`.
  4. **Target Formulation & Scale Experiments (2)**: `run_target_formulation_experiment.py`, `test_target_formulation.py`.
  5. **Leafy Green Quality & Administrative Freeze Audits (8)**: `check_leafy_ratio.py`, `compute_leafy_metrics.py`, `compute_leafy_stale_clean_table.py`, `generate_corrected_leafy_table.py`, `run_leafy_stale_experiment.py`, `scratch_check_leafy.py`, `scratch_check_leafy_exact.py`, `scratch_check_leafy_stale.py`.
  6. **Statistical Tests, CIs, & Metric Repairs (4)**: `update_leaderboard_statistics.py`, `test_h1_repair.py`, `compute_split_integrity.py`, `generate_vegetable_skill_ranking.py`.
  7. **Commodity-Level Disaggregation & Forecasting Support (3)**: `rank_vegetables_lasso.py`, `generate_section9_per_category_forecast.py`, `find_full_prophet_run.py`.
  8. **Exploratory & Verification Scratch Scripts (14)**: `check_splits_detail.py`, `check_stale_diff.py`, `check_test_nan.py`, `inspect_prophet.py`, `scratch_check_lasso_alpha.py`, `scratch_check_lasso_leafy.py`, `scratch_check_naive_run.py`, `scratch_check_runs.py`, `scratch_check_scale2.py`, `scratch_check_val_sample.py`, `scratch_inspect_splits.py`, `scratch_investigate_prophet_diff.py`, `scratch_test_annual_refit_match.py`, `scratch_test_leaderboard_naive.py`.

Crucially, **model selection and hyperparameter optimization were frozen on the training and validation splits**. When refitting models on train + validation for test evaluation, strict temporal purge gaps ($\le 417 - h$) were enforced to eliminate lookahead contamination into the test period ($h=1: 416, h=4: 413, h=8: 409, h=12: 405$).

---

## 2. Test A: Temporal Causality Across All 8 Feature Families

Every feature used in the matrix $X_t$ for forecast origin week $t$ was audited to ensure it only aggregates data strictly on or prior to week $t$:

| Feature Family | Implementation & Causal Guarantee | Status |
| :--- | :--- | :---: |
| **1. Own Price Lags** | $y_{t-k}$ for $k \in \{1, 2, 3, 4, 8, 12, 26, 48\}$ shifted causally ($k \ge 1$). | **PASSED** |
| **2. Rolling Statistics** | Rolling mean/std/min/max over windows $w \in \{4, 8, 12, 26\}$ shifted by $\ge 1$ week so $t$ and $t+h$ are excluded. | **PASSED** |
| **3. Same-Week-Last-Year** | Seasonal YoY ratio $y_{t-1} / y_{t-48}$ uses 48-week historical cycle without lookahead. | **PASSED** |
| **4. Calendar Features** | $\sin/\cos$ cyclical encodings of reporting month and week-of-year at origin timestamp $t$. | **PASSED** |
| **5. Cross-Vegetable / Category** | Market median and category means shifted by $\ge 1$ week ($t-1$) before merging. | **PASSED** |
| **6. Missing Indicators** | Boolean missing flag computed strictly at row timestamp $t$. | **PASSED** |
| **7. is_backfilled** | Historical metadata flag indicating administrative publication fills at $t$. | **PASSED** |
| **8. is_stale_run (Causal Fix)** | Counts consecutive identical observations strictly backward up to origin $t$ (run length $\ge 4$). Forward and centered lookaheads were eliminated. | **PASSED** |

---

## 3. Test B: Feature Ablation Study & High-Scale Pooled Target Diagnosis

### Diagnosis of Own-Lags Persistence Anomaly:
In the preliminary ablation draft, own-lags Lasso at $h=1$ exhibited an MAE of 50.08 Rs (-45.82% skill deficit relative to naive persistence at 34.34 Rs). Preliminary commentary mistakenly claimed that "univariate autoregression cannot match persistence." That statement was mathematically incorrect: a linear model with `lag_1` can reproduce persistence exactly ($y_{t+1} = 1.0 \cdot y_t + 0 \cdot y_{t-k}$).

Diagnostic investigation revealed the true root cause: **scale distortion in pooled raw levels**.
1. **Scale Dominance in Pooled Regressions**: The 32 vegetable varieties span average prices from Rs 30 (gotukola) to over Rs 1,500 (drumstick, green chillies). When pooling all commodities into a single regression on raw levels, L1 penalization ($\lambda \sum |\beta_j|$) applies uniform shrinkage across all features. Feature standardization (`StandardScaler()`) normalizes variance but forces cross-crop shrinkage toward a global pooled intercept, pulling low-price and high-price predictions away from their individual series persistence.
2. **Resolution via Dimensionless Log-Ratio**: Under the log-price-ratio target formulation ($\Delta_{t+h} = \log(y_{t+h} / y_t)$), shrinking all regression coefficients to zero yields $\hat{\Delta}_{t+h} = 0$, which corresponds to $\hat{y}_{t+h} = y_t \cdot \exp(0) = y_t$ (exact persistence).
3. **Re-running with Log-Ratio Target**: As demonstrated below, fitting own-lags Lasso on `log_ratio` immediately recovers positive skill vs persistence at $h=4$ (+4.23%, MASE 0.7149 vs naive 0.7465). Full-feature Lasso on log-ratio yields MASE 0.7367 (+1.31% skill vs naive, matching leaderboard row 114).
4. **Resolution of Calendar Feature Degradation**: In earlier ablation runs, adding calendar features severely degraded performance. Diagnostic tracking isolated this to `week_index` (a monotonically increasing integer from 1 to 464) being inadvertently captured by the `c.startswith("week_")` feature selector. Because `week_index` was linear rather than cyclical, out-of-sample extrapolation into the validation partition (weeks 369–416) acted as an explosive linear trend. Replacing `week_index` with pure cyclical harmonics (`sin_month`, `cos_month`, `sin_woy`, `cos_woy`) completely resolved the degradation.

Every cell in the ablation study was recomputed across both Lasso and LightGBM on the exact standardized leaderboard validation partition ($N=1,528$, Naive MAE 34.34 Rs / MASE 0.3293 at $h=1$; Naive MAE 77.42 Rs / MASE 0.7465 at $h=4$):

| Horizon | Feature Configuration | Features | Evaluation Sample | Naive MAE (Rs) | Naive MASE | Lasso MAE (Rs) | Lasso MASE | Lasso Skill vs Naive (%) | LightGBM MAE (Rs) | LightGBM MASE | LightGBM Skill vs Naive (%) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| $h=1$ | 1. Own-Lags (raw_level) | 8 | Validation (N=1528) | 34.34 | 0.3293 | 50.08 | 0.4802 | -45.82% | 57.97 | 0.5559 | -68.81% |
| $h=1$ | 1. Own-Lags (log_ratio) | 8 | Validation (N=1528) | 34.34 | 0.3293 | 37.92 | 0.3636 | -10.42% | 39.16 | 0.3755 | -14.03% |
| $h=1$ | 2. Own-Lags + Cyclical Calendar (raw_level) [Clean] | 14 | Validation (N=1528) | 34.34 | 0.3293 | 50.11 | 0.4805 | -45.92% | 58.99 | 0.5657 | -71.79% |
| $h=1$ | 2. Own-Lags + Calendar with week_index (raw_level) [Flawed Trend] | 15 | Validation (N=1528) | 34.34 | 0.3293 | 56.64 | 0.5431 | -64.93% | 61.47 | 0.5894 | -78.99% |
| $h=1$ | 2. Own-Lags + Cyclical Calendar (log_ratio) [Clean] | 14 | Validation (N=1528) | 34.34 | 0.3293 | 37.92 | 0.3636 | -10.42% | 39.08 | 0.3747 | -13.79% |
| $h=1$ | 3. Full Features (raw_level) [Leaderboard] | 58 | Validation (N=1528) | 34.34 | 0.3293 | 35.52 | 0.3406 | -3.43% | 39.28 | 0.3767 | -14.40% |
| $h=1$ | 3. Full Features (log_ratio) [Leaderboard] | 58 | Validation (N=1528) | 34.34 | 0.3293 | 37.55 | 0.3601 | -9.35% | 39.17 | 0.3756 | -14.06% |
| $h=4$ | 1. Own-Lags (raw_level) | 8 | Validation (N=1528) | 77.42 | 0.7465 | 81.96 | 0.7903 | -5.87% | 86.83 | 0.8372 | -12.15% |
| $h=4$ | 1. Own-Lags (log_ratio) | 8 | Validation (N=1528) | 77.42 | 0.7465 | 74.14 | 0.7149 | **+4.23%** | 74.15 | 0.7150 | **+4.22%** |
| $h=4$ | 2. Own-Lags + Cyclical Calendar (raw_level) [Clean] | 14 | Validation (N=1528) | 77.42 | 0.7465 | 82.99 | 0.8002 | -7.19% | 90.49 | 0.8725 | -16.88% |
| $h=4$ | 2. Own-Lags + Calendar with week_index (raw_level) [Flawed Trend] | 15 | Validation (N=1528) | 77.42 | 0.7465 | 100.24 | 0.9665 | -29.47% | 108.06 | 1.0419 | -39.57% |
| $h=4$ | 2. Own-Lags + Cyclical Calendar (log_ratio) [Clean] | 14 | Validation (N=1528) | 77.42 | 0.7465 | 74.37 | 0.7171 | **+3.94%** | 74.10 | 0.7145 | **+4.29%** |
| $h=4$ | 3. Full Features (raw_level) [Leaderboard] | 58 | Validation (N=1528) | 77.42 | 0.7465 | 76.49 | 0.7376 | **+1.19%** | 80.56 | 0.7767 | -4.05% |
| $h=4$ | 3. Full Features (log_ratio) [Leaderboard] | 58 | Validation (N=1528) | 77.42 | 0.7465 | 76.41 | 0.7367 | **+1.31%** | 75.92 | 0.7320 | **+1.94%** |

---

## 4. Test C: Placebo Target Shift Test Across All Horizons

To confirm that predictive accuracy originates from authentic causal dynamics rather than pipeline artifacts or target leakage, training targets were shifted forward by $+4$ weeks inside the training partition only. Both the real target and placebo target models were fitted using the exact leaderboard Lasso configuration (`Pipeline(StandardScaler(), Lasso(alpha=alpha))` with CV-tuned $\alpha$ per horizon) and evaluated on the held-out test partition ($N=1,526$):
- **Tuned Hyperparameter $\alpha$**: $h=1: \alpha = 1.5359$, $h=4: \alpha = 3.3947$, $h=8: \alpha = 4.4937$, $h=12: \alpha = 0.6522$.
- **Test Sample**: $N = 1,526$ observations per horizon (Leaderboard Naive test MASE: 0.3035 / 0.8456 / 1.3066 / 1.4032). Real Lasso skill matches the leaderboard exactly (+2.24% at $h=1$, +8.87% at $h=4$, +17.24% at $h=8$, +20.30% at $h=12$).

| Horizon | Tuned $\alpha$ | Naive Test MASE | Real Lasso MASE | Real Lasso $R^2$ | Real Skill vs Naive (%) | Placebo Lasso MASE | Placebo Lasso $R^2$ | Placebo Skill vs Naive (%) | Placebo Skill Retention vs Real |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$h=1$** | 1.5359 | 0.3035 | 0.2967 | 0.9343 | **+2.24%** | 0.5108 | 0.8895 | **-68.30%** | 0.0% |
| **$h=4$** | 3.3947 | 0.8456 | 0.7706 | 0.6874 | **+8.87%** | 0.8403 | 0.6690 | **+0.63%** | **7.1%** |
| **$h=8$** | 4.4937 | 1.3066 | 1.0814 | 0.4829 | **+17.24%** | 1.1069 | 0.4796 | **+15.28%** | **88.7%** |
| **$h=12$** | 0.6522 | 1.4032 | 1.1183 | 0.4714 | **+20.30%** | 1.1948 | 0.4268 | **+14.85%** | **73.1%** |

### Placebo Test Findings & Long-Horizon Baseline Insights:
- **Short Horizons ($h=1, 4$)**: The $+4$-week target shift completely destroys predictive performance relative to naive persistence (placebo skill drops to **-68.30%** at $h=1$ and **+0.63%** at $h=4$, retaining only 7.1% of the Real Lasso's +8.87% skill). This proves strict causal temporal alignment: without true contemporaneous timing, short-term forecasting skill collapses.
- **Positive Placebo Skill at Distant Horizons ($h=8, 12$)**: At $h=8$ and $h=12$, naive persistence ($y_{t+h} \approx y_t$) fails severely (Naive MASE rises to 1.3066 at $h=8$ and 1.4032 at $h=12$, performing 31% to 40% worse than historical series differencing). Under severe persistence breakdown, even a model trained on misaligned targets predicts unconditional commodity central tendencies and annual seasonal cycles. Consequently, the Placebo Lasso model naturally outperforms naive persistence (+15.28% skill at $h=8$, +14.85% at $h=12$), retaining **88.7%** and **73.1%** of the Real Lasso's skill relative to naive persistence.
- **Why Naive Persistence is an Insufficient Long-Horizon Benchmark**: Because naive persistence deteriorates so severely at $h=8$ and $h=12$, outperforming persistence does not prove genuine multi-month dynamic forecasting skill. To establish true predictability at distant horizons, models must be benchmarked against stronger, non-trivial baselines:
  - `rolling_52wk_mean`: Trailing 52-week moving average (Test MASE: 1.0192 at $h=8$, 0.9584 at $h=12$).
  - `seasonal_mean_4yr`: Historical 4-year seasonal average for the same calendar week (Test MASE: 0.7212 at $h=8$, 0.6774 at $h=12$).
  - `ar1_category_mean`: Mean-reverting AR(1) process pulling each commodity toward its category-level mean ($\phi = 0.92$).
  At $h=8$ and $h=12$, advanced models are evaluated against these stronger baselines in the updated leaderboard to verify true incremental value beyond unconditional mean reversion.

---

## 5. Test D: Split Integrity & Purge-Gap Enforcement Audit

To demonstrate that no lookahead leakage exists across split boundaries, splits are strictly defined by **TARGET week** with explicit $h$-week purge gaps separating the training, validation, and test refit partitions:
- **Train Targets**: Terminate at week $369 - h$ (ensuring training target values never reach or overlap the validation window).
- **Validation Targets**: Fixed at weeks 369 to 416 (2024-09-04 to 2025-08-25, 48 weekly reporting periods).
- **Train + Validation Test Refit**: When refitting models on train + validation for held-out test scoring, target weeks are purged to ensure the last target used is strictly $\le 417 - h$ ($h=1: 416, h=4: 413, h=8: 409, h=12: 405$). This guarantees an exact $h$-week purge gap separating the refit training labels from the first test target (week 417).
- **Test Targets**: Fixed at weeks 417 to 464 (2025-09-04 to 2026-08-25, 48 weekly reporting periods).

| Horizon | Split / Regime | Observations ($N$) | Min Origin Wk | Max Origin Wk | Min Target Wk | Max Target Wk | Purge Gap to Next Split |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$h=1$** | Train | 11,194 | 1 | 367 | 2 | 368 | 1 week ($\ge h=1$) |
| $h=1$ | Validation | 1,528 | 368 | 415 | 369 | 416 | 1 week (target disjoint) |
| $h=1$ | Train+Val Test Refit | 13,280 | 1 | 415 | 2 | 416 | 1 week ($\ge h=1$; 0 purged) |
| $h=1$ | Test Evaluation | 1,526 | 416 | 463 | 417 | 464 | N/A (terminal split) |
| **$h=4$** | Train | 11,004 | 1 | 361 | 5 | 365 | **4 weeks ($\ge h=4$)** |
| $h=4$ | Validation | 1,528 | 365 | 412 | 369 | 416 | 1 week (target disjoint) |
| $h=4$ | Train+Val Test Refit | 12,992 | 1 | 409 | 5 | 413 | **4 weeks ($\ge h=4$; 96 purged)** |
| $h=4$ | Test Evaluation | 1,526 | 413 | 460 | 417 | 464 | N/A (terminal split) |
| **$h=8$** | Train | 10,748 | 1 | 353 | 9 | 361 | **8 weeks ($\ge h=8$)** |
| $h=8$ | Validation | 1,528 | 361 | 408 | 369 | 416 | 1 week (target disjoint) |
| $h=8$ | Train+Val Test Refit | 12,608 | 1 | 401 | 9 | 409 | **8 weeks ($\ge h=8$; 224 purged)** |
| $h=8$ | Test Evaluation | 1,526 | 409 | 456 | 417 | 464 | N/A (terminal split) |
| **$h=12$** | Train | 10,492 | 1 | 345 | 13 | 357 | **12 weeks ($\ge h=12$)** |
| $h=12$ | Validation | 1,528 | 357 | 404 | 369 | 416 | 1 week (target disjoint) |
| $h=12$ | Train+Val Test Refit | 12,224 | 1 | 393 | 13 | 405 | **12 weeks ($\ge h=12$; 352 purged)** |
| $h=12$ | Test Evaluation | 1,526 | 405 | 452 | 417 | 464 | N/A (terminal split) |

### Mathematical Explanation: Why Naive Test MASE Changed Under Purged Refitting
A critical question arises: *Why did Naive test MASE shift (0.8500 / 1.2678 / 1.4104 $\to$ 0.8456 / 1.3066 / 1.4032) while its evaluation sample size remained strictly unchanged at $N_{\text{obs}} = 1,526$, given that Naive persistence has no fitted parameters?*

1. **Point Errors Are 100% Numerically Identical**:
   Naive persistence predicts $\hat{y}_{t+h} = y_t$. Across both unpurged and purged pipelines, the test origin prices $y_t$ and realized test prices $y_{t+h}$ are identical. Consequently, Naive test MAE is invariant to 4 decimal places:
   - $h=1$: $\text{MAE} = 31.9100 \text{ Rs}$
   - $h=4$: $\text{MAE} = 89.2600 \text{ Rs}$
   - $h=8$: $\text{MAE} = 133.0800 \text{ Rs}$
   - $h=12$: $\text{MAE} = 152.1800 \text{ Rs}$

2. **MASE Denominator Scaling Effect**:
   Mean Absolute Scaled Error (Hyndman & Koehler, 2006) divides test MAE by the in-sample mean absolute first difference of the training history available prior to test evaluation:
   $$\text{MASE} = \frac{\text{MAE}_{\text{test}}}{\frac{1}{N_{\text{refit}}-1} \sum_{i=2}^{N_{\text{refit}}} |y_i - y_{i-1}|}$$
   In the unpurged pipeline, `y_train_history` included all validation weeks up to week 416 without horizon-specific purging. In the purged pipeline, late validation observations with target $> 417 - h$ are strictly excised ($96$ rows at $h=4$, $224$ rows at $h=8$, $352$ rows at $h=12$).
3. **Denominator Shifts Explain the Entire Delta**:
   - At $h=4$, excising weeks with target $> 413$ shifted the training differencing scale from $105.0118 \to 105.5582 \text{ Rs}$, moving Naive MASE from $89.2600 / 105.0118 = 0.8500$ down to $89.2600 / 105.5582 = 0.8456$.
   - At $h=8$, excising weeks with target $> 409$ shifted the scale from $104.9692 \to 101.8521 \text{ Rs}$, moving Naive MASE from $133.0800 / 104.9692 = 1.2678$ up to $133.0800 / 101.8521 = 1.3066$.
   - At $h=12$, excising weeks with target $> 405$ shifted the scale from $107.8985 \to 108.4521 \text{ Rs}$, moving Naive MASE from $152.1800 / 107.8985 = 1.4104$ down to $152.1800 / 108.4521 = 1.4032$.
Thus, the shift is purely an in-sample scaling normalization consequence of temporal purging, with zero change in test predictions or absolute rupee accuracy.

---

## 6. Hyperparameter Parity Audit: Per-Horizon Tuned Alphas

In earlier diagnostic drafts, hyperparameter selection was incompletely reported:
- Exploratory scripts hardcoded `Lasso(alpha=0.01)` for the log-ratio target.
- Other scripts cited a generic single $\alpha \approx 6.20$ derived from coarse preliminary cross-validation across pooled unstandardized features.

**Resolution Implemented**:
In the unified pipeline, Optuna hyperparameter tuning via expanding-window time-series CV on training data was executed systematically across all four horizons for both target modes:
- **Mode A (`raw_level`)**: Hyperparameters are tuned per horizon to balance feature shrinkage against high-magnitude rupee levels:
  - $h=1$: $\alpha = 1.5359$
  - $h=4$: $\alpha = 3.3947$
  - $h=8$: $\alpha = 4.4937$
  - $h=12$: $\alpha = 0.6522$
- **Mode B (`log_ratio`)**: Tuned parameter converges consistently to $\alpha = 0.01$ across horizons to penalize dimensionless log returns ($\Delta_{t+h} \approx [-0.5, +0.5]$).
- The generic $\alpha \approx 6.20$ was an artifact of exploratory pooling; the frozen per-horizon alphas above represent the true pre-registered Optuna-optimized regularizers applied identically across validation and test refitting.

---

## 7. Audit Summary, Untested Boundaries, and Residual Risks

### What Was Tested:
1. Exact row-level causal alignments for all 8 feature families across all 32 commodities.
2. Complete disk-level temporal truncation across 160 random vegetable test origins (asserting 100% numerical identity).
3. Target decimation via placebo target shifting across all four forecasting horizons ($h \in \{1, 4, 8, 12\}$).
4. Feature ablation benchmarked against naive persistence using identical leaderboard hyperparameters.
5. Strict target-date split enforcement with $h$-week purge gaps preventing training-to-validation lookahead.

### What Was NOT Tested:
1. Source-level data recording accuracy in physical market bulletin offices prior to official digitization.
2. Intra-week price volatility (daily auction fluctuations are unobserved in the 4-week-per-month discretization).
3. Spatial transport arbitrage between regional economic centers (data records aggregate Colombo wholesale/retail quotations).

### Residual Risks:
1. **Macroeconomic Non-Stationarity**: Sudden currency devaluations or import fertilizer bans (as observed in 2022) can induce localized regime changes where historical distributions under-cover until recalibrated.
2. **Administrative Interventions**: Periodic price ceilings on essential commodities (e.g. leafy vegetables during 2020–2023) introduce artificial autocorrelation that differs from market-clearing behavior.
