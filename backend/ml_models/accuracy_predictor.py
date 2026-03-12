"""
Accuracy predictor: second model that predicts surrogate error from antenna parameters.

Used to decide when to run full EM instead of trusting the surrogate (twin-DNN idea).
See: Jibiki et al., "Topology Optimization of Microstrip Lines Using Twin Deep Neural
Networks for Performance Prediction and Accuracy Evaluation."
"""

from typing import List, Optional
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from backend.core.models.schemas import AntennaParameters, EMSimulationResult, SurrogatePrediction
from backend.core.exceptions import ModelError


def extract_features(params: AntennaParameters) -> np.ndarray:
    """Extract 7D feature vector from antenna parameters (same as surrogate)."""
    return np.array([
        params.geometry.length,
        params.geometry.width,
        params.geometry.height,
        params.geometry.feed_x,
        params.geometry.feed_y,
        params.substrate.relative_permittivity,
        params.substrate.loss_tangent,
    ], dtype=np.float64)


def extract_metric_value(obj, metric: str) -> float:
    """Extract scalar metric from EM result or SurrogatePrediction."""
    if metric == "s11_min":
        if hasattr(obj, "s11") and obj.s11 and obj.s11.s11_magnitude:
            return float(min(obj.s11.s11_magnitude))
        return 0.0
    if metric == "gain":
        return float(getattr(obj, "gain", 0.0))
    if metric == "efficiency":
        return float(getattr(obj, "efficiency", 0.0))
    return 0.0


class AccuracyPredictorNN(nn.Module):
    """Small MLP that predicts expected absolute error (MAE) of the surrogate."""

    def __init__(self, input_dim: int = 7, hidden_dims: List[int] = [32, 16], output_dim: int = 1):
        super().__init__()
        layers = []
        prev = input_dim
        for h in hidden_dims:
            layers.append(nn.Linear(prev, h))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.1))
            prev = h
        layers.append(nn.Linear(prev, output_dim))
        layers.append(nn.Softplus())  # ensure positive predicted error
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class AccuracyPredictor:
    """
    Predicts expected surrogate error (MAE) for a given antenna parameter set.
    When predicted_mae > threshold, recommend running full EM.
    """

    def __init__(
        self,
        input_dim: int = 7,
        hidden_dims: List[int] = [32, 16],
        device: str = "cpu",
    ):
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.device = torch.device(device)
        self.model: Optional[AccuracyPredictorNN] = None
        self.scaler_x: Optional[object] = None
        self.trained = False

    def fit(
        self,
        parameters: List[AntennaParameters],
        em_results: List[EMSimulationResult],
        surrogate_predictions: List[SurrogatePrediction],
        metric: str = "s11_min",
        epochs: int = 150,
        batch_size: int = 32,
        lr: float = 0.01,
    ) -> None:
        """
        Train the accuracy predictor on (params, |EM - surrogate|).

        Args:
            parameters: Antenna parameter sets
            em_results: Ground-truth EM results
            surrogate_predictions: Surrogate predictions for the same parameters
            metric: Metric to predict error for ("s11_min", "gain", "efficiency")
            epochs: Training epochs
            batch_size: Batch size
            lr: Learning rate
        """
        from sklearn.preprocessing import StandardScaler

        if len(parameters) != len(em_results) or len(parameters) != len(surrogate_predictions):
            raise ValueError("parameters, em_results, and surrogate_predictions must have same length")

        X = np.stack([extract_features(p) for p in parameters], axis=0).astype(np.float32)
        errors = []
        for em, pred in zip(em_results, surrogate_predictions):
            em_val = extract_metric_value(em, metric)
            pred_val = extract_metric_value(pred, metric)
            errors.append(abs(em_val - pred_val))
        y = np.array(errors, dtype=np.float32).reshape(-1, 1)

        self.scaler_x = StandardScaler()
        X_scaled = self.scaler_x.fit_transform(X)
        self.model = AccuracyPredictorNN(
            input_dim=self.input_dim,
            hidden_dims=self.hidden_dims,
            output_dim=1,
        ).to(self.device)

        dataset = _ErrorDataset(X_scaled, y)
        loader = DataLoader(dataset, batch_size=min(batch_size, len(X)), shuffle=True)
        opt = torch.optim.Adam(self.model.parameters(), lr=lr)

        self.model.train()
        for _ in range(epochs):
            for xb, yb in loader:
                xb = torch.as_tensor(xb, dtype=torch.float32, device=self.device)
                yb = torch.as_tensor(yb, dtype=torch.float32, device=self.device)
                opt.zero_grad()
                out = self.model(xb)
                loss = nn.functional.mse_loss(out, yb)
                loss.backward()
                opt.step()
        self.trained = True

    def predict_mae(self, parameters: AntennaParameters) -> float:
        """
        Predict expected MAE of the surrogate for this parameter set.

        Returns:
            Predicted absolute error (e.g. in dB for s11_min).
        """
        if not self.trained or self.model is None or self.scaler_x is None:
            return 0.0
        self.model.eval()
        x = extract_features(parameters).astype(np.float32).reshape(1, -1)
        x = self.scaler_x.transform(x)
        with torch.no_grad():
            t = torch.as_tensor(x, dtype=torch.float32, device=self.device)
            out = self.model(t)
        return float(out.cpu().numpy().item())

    def recommend_em_run(self, parameters: AntennaParameters, threshold: float) -> bool:
        """True if predicted surrogate error exceeds threshold (run full EM)."""
        return self.predict_mae(parameters) > threshold


class _ErrorDataset(Dataset):
    def __init__(self, X: np.ndarray, y: np.ndarray):
        self.X = torch.from_numpy(X).float()
        self.y = torch.from_numpy(y).float()

    def __len__(self):
        return len(self.X)

    def __getitem__(self, i):
        return self.X[i], self.y[i]
