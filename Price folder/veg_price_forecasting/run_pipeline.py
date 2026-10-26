import sys
import argparse
from pathlib import Path

# Add project root to sys.path
proj_root = Path(__file__).resolve().parent
if str(proj_root) not in sys.path:
    sys.path.insert(0, str(proj_root))

from src.utils import load_config, get_logger
from src.train import run_experiment_pipeline
from src.evaluate import generate_thesis_figures, generate_thesis_tables

logger = get_logger("run_pipeline")

def main():
    parser = argparse.ArgumentParser(description="End-to-End Vegetable Market Price Forecasting Pipeline.")
    parser.add_argument("--smoke-test", action="store_true", help="Run rapid smoke test on 3 vegetables and 2 horizons.")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config.yaml")
    args = parser.parse_args()
    
    cfg = load_config(args.config)
    is_smoke = args.smoke_test
    
    logger.info("="*70)
    logger.info(f"STARTING RESEARCH FORECASTING PIPELINE (Mode: {'SMOKE TEST' if is_smoke else 'FULL RUN'})")
    logger.info("="*70)
    
    df_lead, best_model = run_experiment_pipeline(cfg=cfg, is_smoke=is_smoke)
    
    # Generate figures and tables
    exp_dir = Path(cfg["paths"]["experiments"])
    res_dir = Path(cfg["paths"]["results"])
    generate_thesis_figures(exp_dir, res_dir, cfg=cfg)
    generate_thesis_tables(exp_dir, res_dir)
    
    logger.info("="*70)
    logger.info(f"PIPELINE COMPLETED SUCCESSFULLY! Winning Model: [{best_model}]")
    logger.info("="*70)

if __name__ == "__main__":
    main()
