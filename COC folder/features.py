"""
Compatibility shim: features.py
===============================
Provides CropLagImputer and preprocessor helpers in COC folder root
so that models pickled with 'features' or 'train_evaluate_pipeline'
can be unpickled interchangeably without ModuleNotFoundError.
"""

import sys
from pathlib import Path

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

from train_evaluate_pipeline import (
    CropLagImputer,
    build_preprocessor,
    get_feature_names
)

__all__ = ["CropLagImputer", "build_preprocessor", "get_feature_names"]
