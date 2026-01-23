"""Confidence decay over time."""

from typing import Dict, Any
from datetime import datetime, timedelta
import numpy as np


class ConfidenceDecay:
    """Model confidence decay over time."""
    
    def __init__(self, decay_rate: float = 0.01):
        """
        Initialize confidence decay.
        
        Args:
            decay_rate: Daily decay rate
        """
        self.decay_rate = decay_rate
    
    def calculate_confidence(
        self,
        initial_confidence: float,
        days_since_training: float
    ) -> float:
        """
        Calculate current confidence.
        
        Args:
            initial_confidence: Initial confidence (0-1)
            days_since_training: Days since model was trained
            
        Returns:
            Current confidence
        """
        # Exponential decay
        confidence = initial_confidence * np.exp(-self.decay_rate * days_since_training)
        return float(max(0.0, min(1.0, confidence)))
    
    def should_request_measurement(
        self,
        current_confidence: float,
        threshold: float = 0.7
    ) -> bool:
        """
        Check if measurement should be requested.
        
        Args:
            current_confidence: Current confidence
            threshold: Confidence threshold
            
        Returns:
            True if measurement should be requested
        """
        return current_confidence < threshold



















