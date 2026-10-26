"""
run_all_experiments.py - Master execution runner for the IT4010 research suite.
Runs all 4 families sequentially, executes significance testing, exports leaderboards and figures.
"""

import sys
import time
from pathlib import Path

src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import run_family_a_statistical
import run_family_b_shallow_ml
import run_family_c_deep_learning
import run_family_d_foundation
import run_evaluation_and_significance


def main():
    start_total = time.time()
    print("=" * 80)
    print("LAUNCHING FULL IT4010 EXPERIMENTAL BENCHMARK (FAMILIES A, B, C, D)")
    print("=" * 80)

    # Family A: Statistical & Time-Series
    print("\n>>> PHASE 4: FAMILY A (STATISTICAL & TIME-SERIES) <<<")
    run_family_a_statistical.main()

    # Family B: Shallow ML
    print("\n>>> PHASE 5: FAMILY B (SHALLOW MACHINE LEARNING) <<<")
    run_family_b_shallow_ml.main()

    # Family C: Deep Learning
    print("\n>>> PHASE 6: FAMILY C (DEEP LEARNING TABULAR & SEQUENCE) <<<")
    run_family_c_deep_learning.main()

    # Family D: Foundation & LLM Models
    print("\n>>> PHASE 7: FAMILY D (FOUNDATION & LLM MODELS) <<<")
    run_family_d_foundation.main()

    # Evaluation, Significance & Champion
    print("\n>>> PHASE 8 & 9: EVALUATION, SIGNIFICANCE & CHAMPION PACKAGING <<<")
    run_evaluation_and_significance.main()

    total_duration = time.time() - start_total
    print("\n" + "=" * 80)
    print(f"ALL EXPERIMENTS SUCCESSFULLY EXECUTED IN {total_duration/60:.1f} MINUTES!")
    print("=" * 80)


if __name__ == "__main__":
    main()
