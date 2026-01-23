"""SQLAlchemy database models."""

from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.database.base import Base
import uuid


def generate_id():
    """Generate UUID string."""
    return str(uuid.uuid4())


class AntennaInstance(Base):
    """Antenna instance record."""
    __tablename__ = "antenna_instances"
    
    id = Column(String, primary_key=True, default=generate_id)
    instance_id = Column(String, unique=True, nullable=False, index=True)
    geometry_length = Column(Float, nullable=False)
    geometry_width = Column(Float, nullable=False)
    geometry_height = Column(Float, nullable=False)
    geometry_feed_x = Column(Float, nullable=False)
    geometry_feed_y = Column(Float, nullable=False)
    substrate_type = Column(String, nullable=False)
    substrate_permittivity = Column(Float, nullable=False)
    substrate_loss_tangent = Column(Float, nullable=False)
    substrate_thickness = Column(Float, nullable=False)
    feed_type = Column(String, nullable=False)
    frequency_band = Column(String, nullable=False)
    frequency_min = Column(Float, nullable=False)
    frequency_max = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    instance_metadata = Column(JSON, default=dict)
    
    # Relationships
    em_simulations = relationship("EMSimulation", back_populates="antenna_instance", cascade="all, delete-orphan")
    measurements = relationship("Measurement", back_populates="antenna_instance", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_antenna_params', 'geometry_length', 'geometry_width', 'substrate_permittivity'),
    )


class EMSimulation(Base):
    """EM simulation record."""
    __tablename__ = "em_simulations"
    
    id = Column(String, primary_key=True, default=generate_id)
    simulation_id = Column(String, unique=True, nullable=False, index=True)
    antenna_instance_id = Column(String, ForeignKey("antenna_instances.id"), nullable=False)
    solver_name = Column(String, nullable=False)
    solver_version = Column(String)
    s11_data_path = Column(String)  # Path to S11 data file
    gain = Column(Float)
    efficiency = Column(Float)
    radiation_pattern_path = Column(String)  # Path to pattern data
    simulation_time = Column(Float)  # seconds
    status = Column(String, default="pending")  # pending, running, completed, failed
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    sim_metadata = Column(JSON, default=dict)
    
    # Relationships
    antenna_instance = relationship("AntennaInstance", back_populates="em_simulations")


class Measurement(Base):
    """Physical measurement record."""
    __tablename__ = "measurements"
    
    id = Column(String, primary_key=True, default=generate_id)
    measurement_id = Column(String, unique=True, nullable=False, index=True)
    antenna_instance_id = Column(String, ForeignKey("antenna_instances.id"), nullable=False)
    s11_data_path = Column(String)
    gain = Column(Float)
    efficiency = Column(Float)
    radiation_pattern_path = Column(String)
    temperature = Column(Float)
    humidity = Column(Float)
    operator = Column(String)
    equipment_id = Column(String)
    quality_score = Column(Float)
    measured_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    meas_metadata = Column(JSON, default=dict)
    
    # Relationships
    antenna_instance = relationship("AntennaInstance", back_populates="measurements")
    
    __table_args__ = (
        Index('idx_measurement_time', 'measured_at', 'antenna_instance_id'),
    )


class SurrogateModel(Base):
    """Surrogate model registry."""
    __tablename__ = "surrogate_models"
    
    id = Column(String, primary_key=True, default=generate_id)
    model_name = Column(String, nullable=False, index=True)
    model_version = Column(String, nullable=False)
    model_type = Column(String, nullable=False)  # gaussian_process, neural_network, ensemble
    model_path = Column(String, nullable=False)  # Path to model file
    training_data_hash = Column(String)  # Hash of training data
    performance_metrics = Column(JSON)  # Validation metrics
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)  # 1 = active, 0 = archived
    model_metadata = Column(JSON, default=dict)
    
    __table_args__ = (
        Index('idx_model_name_version', 'model_name', 'model_version', unique=True),
    )


class Prediction(Base):
    """Surrogate model prediction record."""
    __tablename__ = "predictions"
    
    id = Column(String, primary_key=True, default=generate_id)
    prediction_id = Column(String, unique=True, nullable=False, index=True)
    model_id = Column(String, ForeignKey("surrogate_models.id"), nullable=False)
    antenna_instance_id = Column(String, ForeignKey("antenna_instances.id"), nullable=False)
    s11_prediction_path = Column(String)
    gain_prediction = Column(Float)
    efficiency_prediction = Column(Float)
    confidence_intervals = Column(JSON)  # Confidence bounds
    prediction_time = Column(Float)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    pred_metadata = Column(JSON, default=dict)
    
    # Relationships
    model = relationship("SurrogateModel")
    antenna_instance = relationship("AntennaInstance")


class ModelVersion(Base):
    """Model versioning and lineage tracking."""
    __tablename__ = "model_versions"
    
    id = Column(String, primary_key=True, default=generate_id)
    model_id = Column(String, ForeignKey("surrogate_models.id"), nullable=False)
    version_number = Column(String, nullable=False)
    parent_version_id = Column(String, ForeignKey("model_versions.id"))
    training_data_ids = Column(JSON)  # List of EM simulation IDs used
    measurement_ids = Column(JSON)  # List of measurement IDs used
    update_type = Column(String)  # initial, retrain, bayesian_update
    performance_delta = Column(JSON)  # Performance change metrics
    created_at = Column(DateTime, default=datetime.utcnow)
    version_metadata = Column(JSON, default=dict)
    
    # Relationships
    model = relationship("SurrogateModel")
    parent_version = relationship("ModelVersion", remote_side=[id])



















