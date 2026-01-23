"""Neural network surrogate model for fast inference."""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from backend.core.models.schemas import AntennaParameters, EMSimulationResult
from backend.core.exceptions import ModelError


class AntennaDataset(Dataset):
    """Dataset for antenna parameters and results."""
    
    def __init__(self, X: np.ndarray, y: np.ndarray):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)
    
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


class AntennaNeuralNetwork(nn.Module):
    """Neural network for antenna surrogate."""
    
    def __init__(self, input_dim: int = 7, hidden_dims: List[int] = [64, 128, 64], output_dim: int = 1):
        super(AntennaNeuralNetwork, self).__init__()
        
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.2))
            prev_dim = hidden_dim
        
        layers.append(nn.Linear(prev_dim, output_dim))
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x)


class NeuralSurrogate:
    """Neural network surrogate model for fast inference."""
    
    def __init__(
        self,
        input_dim: int = 7,
        hidden_dims: List[int] = [64, 128, 64],
        device: str = "cpu"
    ):
        """
        Initialize neural surrogate.
        
        Args:
            input_dim: Input dimension
            hidden_dims: Hidden layer dimensions
            device: Device ("cpu" or "cuda")
        """
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.device = torch.device(device)
        self.model = None
        self.trained = False
        self.scaler_x = None
        self.scaler_y = None
    
    def _extract_features(self, parameters: AntennaParameters) -> np.ndarray:
        """Extract feature vector."""
        return np.array([
            parameters.geometry.length,
            parameters.geometry.width,
            parameters.geometry.height,
            parameters.geometry.feed_x,
            parameters.geometry.feed_y,
            parameters.substrate.relative_permittivity,
            parameters.substrate.loss_tangent
        ])
    
    def _extract_targets(self, results: List[EMSimulationResult], target: str = "s11_min") -> np.ndarray:
        """Extract target values."""
        values = []
        for result in results:
            if target == "s11_min":
                if result.s11 and result.s11.s11_magnitude:
                    values.append(min(result.s11.s11_magnitude))
                else:
                    values.append(0.0)
            elif target == "gain":
                values.append(result.gain)
            elif target == "efficiency":
                values.append(result.efficiency)
            else:
                raise ValueError(f"Unknown target: {target}")
        return np.array(values)
    
    def fit(
        self,
        parameters: List[AntennaParameters],
        results: List[EMSimulationResult],
        target: str = "s11_min",
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.001
    ) -> None:
        """
        Train neural network.
        
        Args:
            parameters: Training parameters
            results: Training results
            target: Target metric
            epochs: Training epochs
            batch_size: Batch size
            learning_rate: Learning rate
        """
        # Extract features and targets
        X = np.array([self._extract_features(p) for p in parameters])
        y = self._extract_targets(results, target)
        
        # Normalize
        from sklearn.preprocessing import StandardScaler
        self.scaler_x = StandardScaler()
        self.scaler_y = StandardScaler()
        
        X_scaled = self.scaler_x.fit_transform(X)
        y_scaled = self.scaler_y.fit_transform(y.reshape(-1, 1)).flatten()
        
        # Create dataset and dataloader
        dataset = AntennaDataset(X_scaled, y_scaled)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
        
        # Initialize model
        self.model = AntennaNeuralNetwork(
            input_dim=self.input_dim,
            hidden_dims=self.hidden_dims,
            output_dim=1
        ).to(self.device)
        
        # Optimizer and loss
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()
        
        # Training loop
        self.model.train()
        for epoch in range(epochs):
            total_loss = 0
            for batch_x, batch_y in dataloader:
                batch_x = batch_x.to(self.device)
                batch_y = batch_y.to(self.device)
                
                optimizer.zero_grad()
                outputs = self.model(batch_x).squeeze()
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
        
        self.trained = True
    
    def predict(
        self,
        parameters: AntennaParameters,
        return_std: bool = False
    ) -> Tuple[float, Optional[float]]:
        """
        Predict (no uncertainty for neural network alone).
        
        Args:
            parameters: Input parameters
            return_std: Not used (neural network doesn't provide uncertainty)
            
        Returns:
            Tuple of (mean, None)
        """
        if not self.trained:
            raise ModelError("Model must be trained before prediction")
        
        # Extract features
        X = self._extract_features(parameters).reshape(1, -1)
        X_scaled = self.scaler_x.transform(X)
        
        # Convert to tensor
        test_x = torch.FloatTensor(X_scaled).to(self.device)
        
        # Predict
        self.model.eval()
        with torch.no_grad():
            output = self.model(test_x).cpu().numpy()[0, 0]
        
        # Denormalize
        output = self.scaler_y.inverse_transform([[output]])[0, 0]
        
        return float(output), None



















