"""
registry.py - Model registry, manifest tracking, SHA-256 checksums, and load-and-predict verification.
"""

import os
import time
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import joblib


def get_experiments_root() -> Path:
    return Path(__file__).resolve().parent.parent


def generate_run_id(family: str, model_name: str) -> str:
    """Generates a reproducible run identifier."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    rand_salt = hashlib.md5(f"{family}_{model_name}_{time.time()}".encode()).hexdigest()[:6]
    return f"{model_name}_{timestamp}_{rand_salt}"


def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 checksum of a file."""
    if not file_path.exists() or file_path.is_dir():
        return "N/A"
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()


def record_manifest_entry(
    run_id: str,
    family: str,
    model_name: str,
    file_path: Path,
    fold: str = "ALL",
    seed: Optional[int] = None,
    series_key: Optional[str] = None,
    load_test_passed: bool = True,
    notes: str = ""
):
    """Appends an entry to models/model_manifest.csv."""
    root = get_experiments_root()
    manifest_csv = root / "models" / "model_manifest.csv"

    file_size = file_path.stat().st_size if file_path.exists() else 0
    checksum = compute_sha256(file_path) if file_path.exists() else "MISSING"

    entry = {
        "run_id": run_id,
        "family": family,
        "model_name": model_name,
        "fold": fold,
        "seed": seed if seed is not None else "N/A",
        "series_key": series_key if series_key is not None else "ALL",
        "file_path": str(file_path.relative_to(root) if file_path.is_relative_to(root) else file_path),
        "file_size_bytes": file_size,
        "sha256": checksum,
        "load_test_passed": load_test_passed,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "notes": notes
    }

    df_entry = pd.DataFrame([entry])
    if manifest_csv.exists():
        df_entry.to_csv(manifest_csv, mode="a", header=False, index=False)
    else:
        df_entry.to_csv(manifest_csv, index=False)


def record_experiment_run(
    run_id: str,
    family: str,
    model_name: str,
    loso_metrics: Dict[str, Any],
    fc_metrics: Optional[Dict[str, Any]] = None,
    hyperparameters: Optional[Dict[str, Any]] = None,
    runtime_seconds: float = 0.0
):
    """Records master run metrics into results/model_registry.csv."""
    root = get_experiments_root()
    registry_csv = root / "results" / "model_registry.csv"

    entry = {
        "run_id": run_id,
        "family": family,
        "model_name": model_name,
        "runtime_seconds": round(runtime_seconds, 2),
        "LOSO_MAE": loso_metrics.get("MAE", np.nan),
        "LOSO_RMSE": loso_metrics.get("RMSE", np.nan),
        "LOSO_R2": loso_metrics.get("R2", np.nan),
        "LOSO_MAPE": loso_metrics.get("MAPE", np.nan),
        "LOSO_sMAPE": loso_metrics.get("sMAPE", np.nan),
        "LOSO_Log_RMSE": loso_metrics.get("Log_RMSE", np.nan),
        "LOSO_Coverage": loso_metrics.get("Coverage", 1.0),
        "FC_MAE": fc_metrics.get("MAE", np.nan) if fc_metrics else np.nan,
        "FC_RMSE": fc_metrics.get("RMSE", np.nan) if fc_metrics else np.nan,
        "FC_R2": fc_metrics.get("R2", np.nan) if fc_metrics else np.nan,
        "hyperparameters": json.dumps(hyperparameters) if hyperparameters else "{}",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    df_entry = pd.DataFrame([entry])
    if registry_csv.exists():
        df_entry.to_csv(registry_csv, mode="a", header=False, index=False)
    else:
        df_entry.to_csv(registry_csv, index=False)


def is_run_completed(model_name: str, family: str) -> bool:
    """Checks whether a run for model_name already exists in results/model_registry.csv."""
    root = get_experiments_root()
    registry_csv = root / "results" / "model_registry.csv"
    if not registry_csv.exists():
        return False
    df = pd.read_csv(registry_csv)
    return ((df["model_name"] == model_name) & (df["family"] == family)).any()
