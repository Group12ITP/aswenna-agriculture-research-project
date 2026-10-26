"""
models_dl.py - PyTorch tabular and sequence deep learning architectures for IT4010 COC.
Supports MLP with Entity Embeddings, TabNet, FT-Transformer, LSTM, GRU, 1D-CNN, and Transformer.
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.base import BaseEstimator, RegressorMixin
from pytorch_tabnet.tab_model import TabNetRegressor

from features import CropLagImputer


class TabularDataset(Dataset):
    """PyTorch Dataset for Tabular Inputs with Categorical and Continuous Features."""
    def __init__(self, cat_tensor: torch.Tensor, cont_tensor: torch.Tensor, target_tensor: Optional[torch.Tensor] = None):
        self.cats = cat_tensor
        self.conts = cont_tensor
        self.targets = target_tensor

    def __len__(self):
        return len(self.conts)

    def __getitem__(self, idx):
        if self.targets is not None:
            return self.cats[idx], self.conts[idx], self.targets[idx]
        return self.cats[idx], self.conts[idx]


class TabularMLP(nn.Module):
    """MLP with categorical entity embedding layers and continuous feature projections."""
    def __init__(self, cat_cardinalities: List[int], emb_dims: List[int], num_cont: int, hidden_dims: List[int] = [128, 64, 32], dropout: float = 0.2):
        super().__init__()
        self.embeddings = nn.ModuleList([
            nn.Embedding(num_embeddings=c, embedding_dim=d)
            for c, d in zip(cat_cardinalities, emb_dims)
        ])
        total_emb_dim = sum(emb_dims)
        in_dim = total_emb_dim + num_cont

        layers = []
        curr_dim = in_dim
        for h_dim in hidden_dims:
            layers.append(nn.Linear(curr_dim, h_dim))
            layers.append(nn.LayerNorm(h_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            curr_dim = h_dim

        layers.append(nn.Linear(curr_dim, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x_cat: torch.Tensor, x_cont: torch.Tensor) -> torch.Tensor:
        emb_outs = [emb(x_cat[:, i]) for i, emb in enumerate(self.embeddings)]
        x_all = torch.cat(emb_outs + [x_cont], dim=1)
        return self.net(x_all).squeeze(-1)


class FTTransformer(nn.Module):
    """Feature Tokenizer Transformer for Tabular Data."""
    def __init__(self, cat_cardinalities: List[int], num_cont: int, d_token: int = 32, n_heads: int = 4, n_blocks: int = 2, dropout: float = 0.1):
        super().__init__()
        self.cat_embeddings = nn.ModuleList([
            nn.Embedding(c, d_token) for c in cat_cardinalities
        ])
        self.cont_weight = nn.Parameter(torch.randn(num_cont, d_token) * 0.02)
        self.cont_bias = nn.Parameter(torch.zeros(num_cont, d_token))

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_token, nhead=n_heads, dim_feedforward=d_token * 4,
            dropout=dropout, activation="relu", batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_blocks)
        self.head = nn.Linear(d_token, 1)

    def forward(self, x_cat: torch.Tensor, x_cont: torch.Tensor) -> torch.Tensor:
        b_size = x_cont.shape[0]
        cat_tokens = [emb(x_cat[:, i]).unsqueeze(1) for i, emb in enumerate(self.cat_embeddings)]
        cont_tokens = (x_cont.unsqueeze(-1) * self.cont_weight.unsqueeze(0) + self.cont_bias.unsqueeze(0))
        all_tokens = torch.cat(cat_tokens + [cont_tokens], dim=1)
        out = self.transformer(all_tokens)
        pooled = out.mean(dim=1)
        return self.head(pooled).squeeze(-1)


class SequenceModel(nn.Module):
    """Global Sequence Model (LSTM / GRU / 1D-CNN) over seasonal history windows."""
    def __init__(self, model_type: str = "lstm", input_dim: int = 4, hidden_dim: int = 32, num_layers: int = 1):
        super().__init__()
        self.model_type = model_type.lower()
        if self.model_type == "lstm":
            self.rnn = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
            self.head = nn.Linear(hidden_dim, 1)
        elif self.model_type == "gru":
            self.rnn = nn.GRU(input_dim, hidden_dim, num_layers, batch_first=True)
            self.head = nn.Linear(hidden_dim, 1)
        elif self.model_type == "cnn":
            self.conv = nn.Conv1d(input_dim, hidden_dim, kernel_size=2, padding=1)
            self.relu = nn.ReLU()
            self.head = nn.Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.model_type in ["lstm", "gru"]:
            out, _ = self.rnn(x)
            last = out[:, -1, :]
            return self.head(last).squeeze(-1)
        else:
            # CNN expects (Batch, Channels, Length)
            x_perm = x.permute(0, 2, 1)
            feat = self.relu(self.conv(x_perm))
            pooled = feat.mean(dim=-1)
            return self.head(pooled).squeeze(-1)


class TabNetWrapper(BaseEstimator, RegressorMixin):
    """Scikit-Learn wrapper around TabNetRegressor with log1p target transformation."""
    def __init__(self, n_d=8, n_a=8, n_steps=3, max_epochs=120, seed=42, verbose=0):
        self.n_d = n_d
        self.n_a = n_a
        self.n_steps = n_steps
        self.max_epochs = max_epochs
        self.seed = seed
        self.verbose = verbose
        self.model_ = None

    def fit(self, X, y):
        X_arr = np.asarray(X, dtype=np.float32)
        y_arr = np.log1p(np.asarray(y, dtype=np.float32)).reshape(-1, 1)
        self.model_ = TabNetRegressor(
            n_d=self.n_d, n_a=self.n_a, n_steps=self.n_steps,
            seed=self.seed, verbose=self.verbose
        )
        self.model_.fit(
            X_train=X_arr, y_train=y_arr,
            max_epochs=self.max_epochs, patience=15,
            batch_size=64, virtual_batch_size=32
        )
        return self

    def predict(self, X):
        X_arr = np.asarray(X, dtype=np.float32)
        preds = self.model_.predict(X_arr).ravel()
        return np.expm1(np.clip(preds, 0, 18.0))
