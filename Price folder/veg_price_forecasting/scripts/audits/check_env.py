import sys
import pandas as pd
import numpy as np

print("Python executable:", sys.executable)
print("Pandas version:", pd.__version__)
print("Numpy version:", np.__version__)
try:
    import prophet
    print("Prophet version:", prophet.__version__)
except Exception as e:
    print("Prophet import error:", e)

try:
    import lightgbm
    print("LightGBM version:", lightgbm.__version__)
except Exception as e:
    print("LightGBM error:", e)

try:
    import torch
    print("Torch version:", torch.__version__)
except Exception as e:
    print("Torch error:", e)
