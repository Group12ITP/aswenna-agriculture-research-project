import logging
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from pathlib import Path

from ..utils import get_logger

logger = get_logger("src.models.deep_learning")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 1. MLP Architecture
class MLPNet(nn.Module):
    def __init__(self, input_dim, hidden_dims=(128, 64), dropout=0.2):
        super().__init__()
        layers = []
        curr_dim = input_dim
        for h_dim in hidden_dims:
            layers.append(nn.Linear(curr_dim, h_dim))
            layers.append(nn.BatchNorm1d(h_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            curr_dim = h_dim
        layers.append(nn.Linear(curr_dim, 1))
        self.net = nn.Sequential(*layers)
        
    def forward(self, x):
        return self.net(x).squeeze(-1)

# 2. LSTM Forecaster
class LSTMNet(nn.Module):
    def __init__(self, input_dim, hidden_dim=64, num_layers=2, dropout=0.2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim, hidden_size=hidden_dim,
            num_layers=num_layers, batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        
    def forward(self, x):
        if x.dim() == 2:
            x = x.unsqueeze(1)
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :]).squeeze(-1)

# 3. GRU Forecaster
class GRUNet(nn.Module):
    def __init__(self, input_dim, hidden_dim=64, num_layers=2, dropout=0.2):
        super().__init__()
        self.gru = nn.GRU(
            input_size=input_dim, hidden_size=hidden_dim,
            num_layers=num_layers, batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        
    def forward(self, x):
        if x.dim() == 2:
            x = x.unsqueeze(1)
        out, _ = self.gru(x)
        return self.fc(out[:, -1, :]).squeeze(-1)

# 4. TCN (1D Dilated Causal Convolutional Network)
class TCNNet(nn.Module):
    def __init__(self, input_dim, num_channels=(64, 32), kernel_size=3, dropout=0.2):
        super().__init__()
        layers = []
        in_c = 1
        for i, out_c in enumerate(num_channels):
            dilation = 2 ** i
            padding = (kernel_size - 1) * dilation
            conv = nn.Conv1d(in_c, out_c, kernel_size, padding=padding, dilation=dilation)
            layers.append(conv)
            layers.append(nn.BatchNorm1d(out_c))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            in_c = out_c
        self.conv_net = nn.Sequential(*layers)
        self.head = nn.Linear(num_channels[-1] * input_dim, 1)
        
    def forward(self, x):
        if x.dim() == 2:
            x = x.unsqueeze(1)
        feat = self.conv_net(x)
        feat = feat[:, :, :x.size(2)]
        flat = feat.reshape(feat.size(0), -1)
        return self.head(flat).squeeze(-1)

# 5. N-BEATS Style Basis Expansion Block
class NBeatsNet(nn.Module):
    def __init__(self, input_dim, hidden_dim=128, num_blocks=3):
        super().__init__()
        self.blocks = nn.ModuleList([
            nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, 1)
            ) for _ in range(num_blocks)
        ])
        
    def forward(self, x):
        out = 0.0
        for block in self.blocks:
            pred = block(x).squeeze(-1)
            out = out + pred
        return out

# 6. Transformer Forecaster
class TransformerNet(nn.Module):
    def __init__(self, input_dim, d_model=64, nhead=4, num_layers=2, dropout=0.2):
        super().__init__()
        self.input_proj = nn.Linear(input_dim, d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, dim_feedforward=d_model*2,
            dropout=dropout, batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.head = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        
    def forward(self, x):
        if x.dim() == 2:
            x = x.unsqueeze(1)
        h = self.input_proj(x)
        t_out = self.transformer(h)
        return self.head(t_out[:, -1, :]).squeeze(-1)

# 7. N-HiTS (Neural Hierarchical Interpolation for Time Series)
class NHiTSNet(nn.Module):
    """
    N-HiTS block with multi-rate pooling to capture multi-scale agricultural cycles
    (fast weekly price swings vs slow seasonal trends).
    """
    def __init__(self, input_dim, hidden_dim=64):
        super().__init__()
        # Rate 1: High frequency (stride 1)
        self.block_high = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        # Rate 2: Medium frequency (stride 2 pooling)
        self.pool_med = nn.AvgPool1d(kernel_size=2, stride=2)
        med_dim = input_dim // 2
        self.block_med = nn.Sequential(
            nn.Linear(med_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        # Rate 3: Low frequency (stride 4 pooling)
        self.pool_low = nn.AvgPool1d(kernel_size=4, stride=4)
        low_dim = input_dim // 4
        self.block_low = nn.Sequential(
            nn.Linear(low_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        
    def forward(self, x):
        # High-frequency pass
        out_high = self.block_high(x).squeeze(-1)
        
        # Medium-frequency pass
        x_med = self.pool_med(x.unsqueeze(1)).squeeze(1)
        out_med = self.block_med(x_med).squeeze(-1)
        
        # Low-frequency pass
        x_low = self.pool_low(x.unsqueeze(1)).squeeze(1)
        out_low = self.block_low(x_low).squeeze(-1)
        
        return out_high + out_med + out_low

# 8. TFT-Lite (Temporal Fusion Transformer Block)
class GatedResidualNetwork(nn.Module):
    def __init__(self, d_model, dropout=0.1):
        super().__init__()
        self.fc1 = nn.Linear(d_model, d_model)
        self.elu = nn.ELU()
        self.fc2 = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)
        self.gate = nn.Linear(d_model, d_model)
        self.sigmoid = nn.Sigmoid()
        self.layer_norm = nn.LayerNorm(d_model)
        
    def forward(self, x):
        h = self.elu(self.fc1(x))
        h = self.dropout(self.fc2(h))
        g = self.sigmoid(self.gate(x))
        return self.layer_norm(x + g * h)

class TFTLiteNet(nn.Module):
    """
    Temporal Fusion Transformer with Gated Residual Networks,
    Variable Selection, and Self-Attention.
    """
    def __init__(self, input_dim, d_model=64, nhead=4, dropout=0.1):
        super().__init__()
        self.input_proj = nn.Linear(input_dim, d_model)
        self.vsn_grn = GatedResidualNetwork(d_model, dropout=dropout)
        self.vsn_gate = nn.Linear(d_model, d_model)
        
        self.attn = nn.MultiheadAttention(embed_dim=d_model, num_heads=nhead, batch_first=True)
        self.post_attn_grn = GatedResidualNetwork(d_model, dropout=dropout)
        self.head = nn.Linear(d_model, 1)
        
    def forward(self, x):
        # x: (batch, input_dim) -> project to d_model
        h = self.input_proj(x)
        # Variable selection via GRN
        h_selected = self.vsn_grn(h)
        gate = torch.sigmoid(self.vsn_gate(h))
        h = gate * h_selected
        
        # Reshape for attention (batch, seq_len=1, d_model)
        h_seq = h.unsqueeze(1)
        attn_out, _ = self.attn(h_seq, h_seq, h_seq)
        h_fused = self.post_attn_grn(attn_out.squeeze(1) + h)
        return self.head(h_fused).squeeze(-1)

# Global history storage for learning curves
DL_LEARNING_HISTORIES = {}

# Unified PyTorch Estimator Wrapper (Scikit-Learn Interface)
class PyTorchForecaster:
    """
    Scikit-learn compatible wrapper for all PyTorch architectures.
    Operates on log prices with Huber loss and per-series scaling.
    """
    def __init__(self, arch="mlp", lr=1e-3, epochs=35, batch_size=128, weight_decay=1e-4, params=None):
        self.arch = arch
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.weight_decay = weight_decay
        self.params = params or {}
        self.model = None
        self.scaler = StandardScaler()
        self.y_scaler = StandardScaler()
        self.train_losses = []
        self.val_losses = []
        self.best_epoch = 0
        
    def _create_model(self, input_dim):
        if self.arch == "mlp":
            return MLPNet(input_dim, hidden_dims=self.params.get("hidden_dims", (128, 64)))
        elif self.arch == "lstm":
            return LSTMNet(input_dim, hidden_dim=self.params.get("hidden_dim", 64))
        elif self.arch == "gru":
            return GRUNet(input_dim, hidden_dim=self.params.get("hidden_dim", 64))
        elif self.arch == "tcn_1d":
            return TCNNet(input_dim, num_channels=self.params.get("num_channels", (64, 32)))
        elif self.arch == "nbeats":
            return NBeatsNet(input_dim, hidden_dim=self.params.get("hidden_dim", 128))
        elif self.arch == "transformer":
            return TransformerNet(input_dim, d_model=self.params.get("d_model", 64))
        elif self.arch == "nhits":
            return NHiTSNet(input_dim, hidden_dim=self.params.get("hidden_dim", 64))
        elif self.arch == "tft_lite":
            return TFTLiteNet(input_dim, d_model=self.params.get("d_model", 64))
        else:
            raise ValueError(f"Unknown deep learning architecture: {self.arch}")
            
    def fit(self, X, y, X_val=None, y_val=None):
        X_scaled = self.scaler.fit_transform(X)
        # Transform raw price target to log price
        y_raw = np.array(y).reshape(-1, 1)
        valid_mask = pd.notna(y_raw.ravel())
        y_log = np.log(np.clip(y_raw[valid_mask], a_min=1.0, a_max=None))
        y_scaled = self.y_scaler.fit_transform(y_log)
        
        X_clean = torch.tensor(X_scaled[valid_mask], dtype=torch.float32)
        y_clean = torch.tensor(y_scaled.ravel(), dtype=torch.float32)
        
        dataset = TensorDataset(X_clean, y_clean)
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        
        # Validation setup if provided
        has_val = X_val is not None and y_val is not None
        if has_val:
            X_val_scaled = self.scaler.transform(X_val)
            y_val_raw = np.array(y_val).reshape(-1, 1)
            val_valid = pd.notna(y_val_raw.ravel())
            y_val_log = np.log(np.clip(y_val_raw[val_valid], a_min=1.0, a_max=None))
            y_val_scaled = self.y_scaler.transform(y_val_log)
            x_val_t = torch.tensor(X_val_scaled[val_valid], dtype=torch.float32).to(device)
            y_val_t = torch.tensor(y_val_scaled.ravel(), dtype=torch.float32).to(device)
            
        self.model = self._create_model(X.shape[1]).to(device)
        optimizer = optim.AdamW(self.model.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        criterion = nn.HuberLoss() # Robust to price spikes
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=4)
        
        best_metric = float("inf")
        best_weights = None
        patience = 7
        patience_counter = 0
        
        self.train_losses = []
        self.val_losses = []
        
        for epoch in range(self.epochs):
            self.model.train()
            total_loss = 0.0
            for batch_x, batch_y in loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                optimizer.zero_grad()
                pred = self.model(batch_x)
                loss = criterion(pred, batch_y)
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                total_loss += loss.item() * len(batch_y)
                
            avg_tr_loss = total_loss / len(dataset)
            self.train_losses.append(round(avg_tr_loss, 5))
            
            # Validation loss evaluation
            if has_val:
                self.model.eval()
                with torch.no_grad():
                    val_pred = self.model(x_val_t)
                    avg_val_loss = criterion(val_pred, y_val_t).item()
                self.val_losses.append(round(avg_val_loss, 5))
                eval_metric = avg_val_loss
            else:
                eval_metric = avg_tr_loss
                self.val_losses.append(round(avg_tr_loss, 5))
                
            scheduler.step(eval_metric)
            
            if eval_metric < best_metric:
                best_metric = eval_metric
                self.best_epoch = epoch + 1
                best_weights = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    break
                    
        if best_weights:
            self.model.load_state_dict({k: v.to(device) for k, v in best_weights.items()})
            
        DL_LEARNING_HISTORIES[self.arch] = {
            "train_losses": self.train_losses,
            "val_losses": self.val_losses,
            "epochs_run": len(self.train_losses),
            "best_epoch": self.best_epoch
        }
        return self
        
    def predict(self, X):
        self.model.eval()
        X_scaled = self.scaler.transform(X)
        tensor_x = torch.tensor(X_scaled, dtype=torch.float32).to(device)
        with torch.no_grad():
            preds_norm = self.model(tensor_x).cpu().numpy().reshape(-1, 1)
        preds_log = self.y_scaler.inverse_transform(preds_norm).ravel()
        # Invert log transform back to price
        preds_unscaled = np.exp(preds_log)
        return np.clip(preds_unscaled, a_min=0.0, a_max=None)

def plot_dl_learning_curves(save_path="results/figures/dl_learning_curves.png"):
    """Plot multi-panel training and validation loss curves for all deep learning models."""
    if not DL_LEARNING_HISTORIES:
        return
        
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    n_models = len(DL_LEARNING_HISTORIES)
    ncols = min(4, n_models)
    nrows = int(np.ceil(n_models / ncols))
    
    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3.5 * nrows), sharey=False)
    axes = np.array(axes).reshape(-1)
    
    for i, (arch, hist) in enumerate(DL_LEARNING_HISTORIES.items()):
        ax = axes[i]
        tr_loss = hist["train_losses"]
        vl_loss = hist["val_losses"]
        eps = range(1, len(tr_loss) + 1)
        ax.plot(eps, tr_loss, label="Train Loss (Huber)", color="#2563eb", linewidth=1.8)
        ax.plot(eps, vl_loss, label="Val Loss (Huber)", color="#dc2626", linewidth=1.8, linestyle="--")
        ax.axvline(hist["best_epoch"], color="#059669", linestyle=":", label=f"Best Ep ({hist['best_epoch']})")
        ax.set_title(f"{arch.upper()}", fontsize=11, fontweight="bold")
        ax.set_xlabel("Epoch", fontsize=9)
        ax.set_ylabel("Loss", fontsize=9)
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(True, alpha=0.3)
        
    # Hide unused subplots
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])
        
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()
    logger.info(f"Saved DL learning curves to {save_path}")
