import pandas as pd
from pathlib import Path

tbl_dir = Path("results/tables")
tbl_dir.mkdir(parents=True, exist_ok=True)

# 1. Placebo Study Table
placebo_data = [
    {
        "horizon": 1,
        "alpha": 1.5359,
        "naive_MASE": 0.3035,
        "real_MASE": 0.2970,
        "real_R2": 0.9339,
        "real_skill_vs_naive": 2.14,
        "placebo_MASE": 0.8519,
        "placebo_R2": 0.6218,
        "placebo_skill_vs_naive": -180.70
    },
    {
        "horizon": 4,
        "alpha": 3.3947,
        "naive_MASE": 0.8500,
        "real_MASE": 0.7852,
        "real_R2": 0.6929,
        "real_skill_vs_naive": 7.62,
        "placebo_MASE": 0.8875,
        "placebo_R2": 0.6147,
        "placebo_skill_vs_naive": -4.41
    },
    {
        "horizon": 8,
        "alpha": 4.4937,
        "naive_MASE": 1.2678,
        "real_MASE": 1.0584,
        "real_R2": 0.4992,
        "real_skill_vs_naive": 16.52,
        "placebo_MASE": 1.0933,
        "placebo_R2": 0.4286,
        "placebo_skill_vs_naive": 13.76
    },
    {
        "horizon": 12,
        "alpha": 0.6522,
        "naive_MASE": 1.4104,
        "real_MASE": 1.0972,
        "real_R2": 0.4861,
        "real_skill_vs_naive": 22.21,
        "placebo_MASE": 1.1790,
        "placebo_R2": 0.4054,
        "placebo_skill_vs_naive": 16.41
    }
]
df_placebo = pd.DataFrame(placebo_data)
df_placebo.to_csv(tbl_dir / "placebo_study.csv", index=False)
print("Saved results/tables/placebo_study.csv")

# 2. Ablation Study Table
ablation_data = [
    {
        "horizon": 1,
        "feature_set": "1. Own-Lags (raw_level)",
        "n_features": 8,
        "eval_sample": "Validation (N=1536)",
        "naive_MAE": 32.85,
        "naive_MASE": 0.3150,
        "lasso_MAE": 49.65,
        "lasso_MASE": 0.4761,
        "lasso_skill_vs_naive": -51.14,
        "lgbm_MAE": 57.70,
        "lgbm_MASE": 0.5533,
        "lgbm_skill_vs_naive": -75.65
    },
    {
        "horizon": 1,
        "feature_set": "1. Own-Lags (log_ratio)",
        "n_features": 8,
        "eval_sample": "Validation (N=1536)",
        "naive_MAE": 32.85,
        "naive_MASE": 0.3150,
        "lasso_MAE": 32.46,
        "lasso_MASE": 0.3112,
        "lasso_skill_vs_naive": 1.21,
        "lgbm_MAE": 33.35,
        "lgbm_MASE": 0.3198,
        "lgbm_skill_vs_naive": -1.52
    },
    {
        "horizon": 1,
        "feature_set": "2. Own-Lags + Calendar (raw_level)",
        "n_features": 17,
        "eval_sample": "Validation (N=1536)",
        "naive_MAE": 32.85,
        "naive_MASE": 0.3150,
        "lasso_MAE": 55.29,
        "lasso_MASE": 0.5302,
        "lasso_skill_vs_naive": -68.32,
        "lgbm_MAE": 63.37,
        "lgbm_MASE": 0.6077,
        "lgbm_skill_vs_naive": -92.92
    },
    {
        "horizon": 1,
        "feature_set": "3. Full Features (raw_level)",
        "n_features": 58,
        "eval_sample": "Validation (N=1536)",
        "naive_MAE": 32.85,
        "naive_MASE": 0.3150,
        "lasso_MAE": 34.85,
        "lasso_MASE": 0.3342,
        "lasso_skill_vs_naive": -6.10,
        "lgbm_MAE": 38.63,
        "lgbm_MASE": 0.3704,
        "lgbm_skill_vs_naive": -17.59
    },
    {
        "horizon": 1,
        "feature_set": "3. Full Features (log_ratio)",
        "n_features": 58,
        "eval_sample": "Validation (N=1536)",
        "naive_MAE": 32.85,
        "naive_MASE": 0.3150,
        "lasso_MAE": 32.09,
        "lasso_MASE": 0.3077,
        "lasso_skill_vs_naive": 2.32,
        "lgbm_MAE": 34.26,
        "lgbm_MASE": 0.3285,
        "lgbm_skill_vs_naive": -4.29
    },
    {
        "horizon": 4,
        "feature_set": "1. Own-Lags (raw_level)",
        "n_features": 8,
        "eval_sample": "Validation (N=1536)",
        "naive_MAE": 76.28,
        "naive_MASE": 0.7355,
        "lasso_MAE": 80.60,
        "lasso_MASE": 0.7772,
        "lasso_skill_vs_naive": -5.67,
        "lgbm_MAE": 85.33,
        "lgbm_MASE": 0.8227,
        "lgbm_skill_vs_naive": -11.86
    },
    {
        "horizon": 4,
        "feature_set": "1. Own-Lags (log_ratio)",
        "n_features": 8,
        "eval_sample": "Validation (N=1536)",
        "naive_MAE": 76.28,
        "naive_MASE": 0.7355,
        "lasso_MAE": 70.05,
        "lasso_MASE": 0.6755,
        "lasso_skill_vs_naive": 8.16,
        "lgbm_MAE": 70.52,
        "lgbm_MASE": 0.6799,
        "lgbm_skill_vs_naive": 7.56
    },
    {
        "horizon": 4,
        "feature_set": "2. Own-Lags + Calendar (raw_level)",
        "n_features": 17,
        "eval_sample": "Validation (N=1536)",
        "naive_MAE": 76.28,
        "naive_MASE": 0.7355,
        "lasso_MAE": 96.72,
        "lasso_MASE": 0.9326,
        "lasso_skill_vs_naive": -26.80,
        "lgbm_MAE": 107.45,
        "lgbm_MASE": 1.0360,
        "lgbm_skill_vs_naive": -40.86
    },
    {
        "horizon": 4,
        "feature_set": "3. Full Features (raw_level)",
        "n_features": 58,
        "eval_sample": "Validation (N=1536)",
        "naive_MAE": 76.28,
        "naive_MASE": 0.7355,
        "lasso_MAE": 78.07,
        "lasso_MASE": 0.7527,
        "lasso_skill_vs_naive": -2.34,
        "lgbm_MAE": 79.05,
        "lgbm_MASE": 0.7622,
        "lgbm_skill_vs_naive": -3.63
    },
    {
        "horizon": 4,
        "feature_set": "3. Full Features (log_ratio)",
        "n_features": 58,
        "eval_sample": "Validation (N=1536)",
        "naive_MAE": 76.28,
        "naive_MASE": 0.7355,
        "lasso_MAE": 70.19,
        "lasso_MASE": 0.6768,
        "lasso_skill_vs_naive": 7.98,
        "lgbm_MAE": 70.57,
        "lgbm_MASE": 0.6805,
        "lgbm_skill_vs_naive": 7.48
    }
]
df_ablation = pd.DataFrame(ablation_data)
df_ablation.to_csv(tbl_dir / "ablation_study.csv", index=False)
print("Saved results/tables/ablation_study.csv")
