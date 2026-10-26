# IT4010 Research Experiments Suite: Agricultural Cost of Cultivation (COC) Prediction

## Overview
This directory contains the independent research-experiment benchmark comparing **Statistical, Shallow ML, Deep Learning, and LLM / Foundation Models** on Sri Lanka agricultural cost data under identical cross-validation protocols (Leave-One-Season-Year-Out LOSO and Forward-Chaining Rolling-Origin).

## Architecture Map
- `config/`: YAML files configuring dataset paths, cross-validation folds, and hyperparameter search grids.
- `src/`: Modular reusable research modules (`data.py`, `features.py`, `cv.py`, `metrics.py`, `models_stat.py`, `models_ml.py`, `models_dl.py`, `models_foundation.py`, `models_llm.py`, `statistical_tests.py`, `plotting.py`, `registry.py`).
- `notebooks/`: Executed Colab-style notebooks (`00` to `06`) with interactive analyses, explanations, and outputs.
- `experiments/`: Complete artifact storage organized by `<family>/<model_name>/<run_id>/`.
- `results/`: Aggregated leaderboards, per-regime and per-crop tables, and high-resolution figures.
- `models/`: Exported candidates, manifest with SHA-256 checksums, and versioned champion candidate.
- `reports/`: Paper-style academic research report (`modelling_report.md`).

## Reproduction Instructions
1. Run smoke tests:
   ```bash
   python src/smoke_test.py
   ```
2. Run full benchmark pipelines by family or execute all notebooks in `notebooks/` sequentially from `00` to `06`.
3. Check `results/leaderboard_loso.csv` and `models/model_manifest.csv` for verified metrics and SHA-256 checksums.
