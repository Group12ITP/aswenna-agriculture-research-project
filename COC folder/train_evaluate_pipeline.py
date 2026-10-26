"""
Root compatibility shim for train_evaluate_pipeline
===================================================
Re-exports all pipeline classes, functions, and symbols from scripts/train_evaluate_pipeline.py.
This ensures unpickling of joblib models (e.g. best_model_pipeline.pkl) referencing
'train_evaluate_pipeline.CropLagImputer' continues to work seamlessly without breakage.
"""

import sys
from pathlib import Path

_WORKSPACE = Path(__file__).resolve().parent
_SCRIPTS_DIR = _WORKSPACE / "scripts"

if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# Re-export all symbols from the implementation in scripts/
from scripts.train_evaluate_pipeline import (  # noqa: F401
    CropLagImputer,
    build_preprocessor,
    get_feature_names,
    main,
)
from scripts.train_evaluate_pipeline import *  # noqa: F401, F403

if __name__ == "__main__":
    main()
