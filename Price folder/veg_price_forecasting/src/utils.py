import os
import sys
import random
import hashlib
import logging
from datetime import datetime
from pathlib import Path
import yaml
import numpy as np
import torch

def set_seeds(seed=42):
    """Ensure full reproducibility across Python, NumPy, and PyTorch."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

def load_config(config_path="config.yaml"):
    """Load and resolve config dictionary."""
    path = Path(config_path)
    if not path.exists():
        # Fallback to current script directory parent
        alt_path = Path(__file__).resolve().parent.parent / "config.yaml"
        if alt_path.exists():
            path = alt_path
        else:
            raise FileNotFoundError(f"Configuration file not found at {config_path} or {alt_path}")
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg

def get_logger(name, log_file=None, level=logging.INFO):
    """Construct dual console/file logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        # File handler
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    return logger

def compute_file_hash(filepath):
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def generate_run_id(model_name, horizon):
    """Generate a clean timestamped experiment run ID."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{ts}_{model_name}_h{horizon}"
