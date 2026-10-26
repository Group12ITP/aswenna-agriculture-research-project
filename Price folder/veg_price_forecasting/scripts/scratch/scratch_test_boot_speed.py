import time
import numpy as np
from src.metrics import block_bootstrap_mase

yt = np.random.randn(1528)
yp = yt + np.random.randn(1528)*0.5
weeks = np.repeat(np.arange(369, 417), 32)[:1528]
train_hist = np.random.randn(11000)

t0 = time.time()
res = block_bootstrap_mase(yt, yp, y_train_history=train_hist, week_indices=weeks, n_boot=250)
print("Bootstrap 250 took:", round(time.time() - t0, 4), "s")
print("Result:", res)
