"""Gaussian Process surrogate model with uncertainty quantification."""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import torch

# PyTorch 2.x removed torch.symeig; gpytorch still uses it in lanczos. Use linalg.eigh instead.
def _symeig_compat(A, eigenvectors=False, upper=True):
    uplo = "U" if upper else "L"
    A_cpu = A.cpu() if A.is_cuda else A
    if eigenvectors:
        L, V = torch.linalg.eigh(A_cpu, UPLO=uplo)
        if A.is_cuda:
            L, V = L.to(A.device), V.to(A.device)
        return L, V
    L = torch.linalg.eigvalsh(A_cpu, UPLO=uplo)
    if A.is_cuda:
        L = L.to(A.device)
    return L, torch.empty(0, device=A.device, dtype=A.dtype)


try:
    torch.symeig(torch.eye(2), eigenvectors=True)
except (RuntimeError, AttributeError):
    torch.symeig = _symeig_compat

import gpytorch
from gpytorch.models import ExactGP
from gpytorch.means import ConstantMean
from gpytorch.kernels import ScaleKernel, MaternKernel
from gpytorch.likelihoods import GaussianLikelihood
from gpytorch.distributions import MultivariateNormal

from backend.core.models.schemas import AntennaParameters, EMSimulationResult, S11Data
from backend.core.exceptions import ModelError


class AntennaGPModel(ExactGP):
    """Gaussian Process model for antenna surrogate."""
    
    def __init__(self, train_x, train_y, likelihood):
        super(AntennaGPModel, self).__init__(train_x, train_y, likelihood)
        self.mean_module = ConstantMean()
        self.covar_module = ScaleKernel(MaternKernel(nu=2.5))
    
    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return MultivariateNormal(mean_x, covar_x)


class GaussianProcessSurrogate:
    """Gaussian Process surrogate model with uncertainty quantification."""
    
    def __init__(
        self,
        input_dim: int = 7,
        device: str = "cpu"
    ):
        """
        Initialize GP surrogate.
        
        Args:
            input_dim: Input dimension (number of parameters)
            device: Device ("cpu" or "cuda")
        """
        self.input_dim = input_dim
        self.device = torch.device(device)
        self.model = None
        self.likelihood = None
        self.trained = False
        self.scaler_x = None
        self.scaler_y = None
    
    def _extract_features(self, parameters: AntennaParameters) -> np.ndarray:
        """Extract feature vector from parameters."""
        return np.array([
            parameters.geometry.length,
            parameters.geometry.width,
            parameters.geometry.height,
            parameters.geometry.feed_x,
            parameters.geometry.feed_y,
            parameters.substrate.relative_permittivity,
            parameters.substrate.loss_tangent
        ])
    
    def _extract_targets(self, results: List[EMSimulationResult]) -> Dict[str, np.ndarray]:
        """Extract target values from results."""
        s11_min = []
        gain = []
        efficiency = []
        
        for result in results:
            if result.s11 and result.s11.s11_magnitude:
                s11_min.append(min(result.s11.s11_magnitude))
            else:
                s11_min.append(0.0)
            gain.append(result.gain)
            efficiency.append(result.efficiency)
        
        return {
            "s11_min": np.array(s11_min),
            "gain": np.array(gain),
            "efficiency": np.array(efficiency)
        }
    
    def fit(
        self,
        parameters: List[AntennaParameters],
        results: List[EMSimulationResult],
        target: str = "s11_min"
    ) -> None:
        """
        Train GP model.
        
        Args:
            parameters: Training parameter sets
            results: Training simulation results
            target: Target metric ("s11_min", "gain", "efficiency")
        """
        # Extract features and targets
        X = np.array([self._extract_features(p) for p in parameters])
        targets = self._extract_targets(results)
        y = targets[target]
        
        # Normalize
        from sklearn.preprocessing import StandardScaler
        self.scaler_x = StandardScaler()
        self.scaler_y = StandardScaler()
        
        X_scaled = self.scaler_x.fit_transform(X)
        y_scaled = self.scaler_y.fit_transform(y.reshape(-1, 1)).flatten()
        
        # Convert to tensors
        train_x = torch.FloatTensor(X_scaled).to(self.device)
        train_y = torch.FloatTensor(y_scaled).to(self.device)
        
        # Initialize model
        self.likelihood = GaussianLikelihood().to(self.device)
        self.model = AntennaGPModel(train_x, train_y, self.likelihood).to(self.device)
        
        # Set to training mode
        self.model.train()
        self.likelihood.train()
        
        # Optimizer
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.1)
        
        # Training loop
        mll = gpytorch.mlls.ExactMarginalLogLikelihood(self.likelihood, self.model)
        
        for i in range(50):  # Training iterations
            optimizer.zero_grad()
            output = self.model(train_x)
            loss = -mll(output, train_y)
            loss.backward()
            optimizer.step()
        
        self.trained = True
    
    def predict(
        self,
        parameters: AntennaParameters,
        return_std: bool = True
    ) -> Tuple[float, Optional[float]]:
        """
        Predict with uncertainty.
        
        Args:
            parameters: Input parameters
            return_std: Return standard deviation
            
        Returns:
            Tuple of (mean, std) or (mean, None)
        """
        if not self.trained:
            raise ModelError("Model must be trained before prediction")
        
        # Extract features
        X = self._extract_features(parameters).reshape(1, -1)
        X_scaled = self.scaler_x.transform(X)
        
        # Convert to tensor
        test_x = torch.FloatTensor(X_scaled).to(self.device)
        
        # Set to evaluation mode
        self.model.eval()
        self.likelihood.eval()
        
        with torch.no_grad(), gpytorch.settings.fast_pred_var():
            observed_pred = self.likelihood(self.model(test_x))
            mean = observed_pred.mean.cpu().numpy()[0]
            std = observed_pred.stddev.cpu().numpy()[0] if return_std else None
        
        # Denormalize
        mean = self.scaler_y.inverse_transform([[mean]])[0, 0]
        if std is not None:
            std = std * self.scaler_y.scale_[0]  # Approximate denormalization
        
        return float(mean), float(std) if std is not None else None



















