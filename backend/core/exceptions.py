"""Custom exceptions for antenna digital twin system."""


class AntennaTwinException(Exception):
    """Base exception for antenna digital twin system."""
    pass


class ConfigurationError(AntennaTwinException):
    """Configuration-related errors."""
    pass


class ValidationError(AntennaTwinException):
    """Data validation errors."""
    pass


class EMSolverError(AntennaTwinException):
    """EM solver execution errors."""
    pass


class SolverNotAvailableError(EMSolverError):
    """Requested EM solver is not available."""
    pass


class SimulationTimeoutError(EMSolverError):
    """EM simulation exceeded timeout."""
    pass


class MeasurementError(AntennaTwinException):
    """Measurement data processing errors."""
    pass


class ModelError(AntennaTwinException):
    """ML model related errors."""
    pass


class ModelNotFoundError(ModelError):
    """Requested model not found."""
    pass


class ModelInferenceError(ModelError):
    """Model inference errors."""
    pass


class DatabaseError(AntennaTwinException):
    """Database operation errors."""
    pass


class OptimizationError(AntennaTwinException):
    """Optimization engine errors."""
    pass



















