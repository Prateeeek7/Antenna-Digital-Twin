"""Antenna instance CRUD API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from backend.database.base import get_db
from backend.database.models import AntennaInstance
from backend.core.models.schemas import AntennaParameters
from backend.core.exceptions import MeasurementError

router = APIRouter(prefix="/antenna-instances", tags=["Antenna Instances"])


def antenna_params_to_db(instance_id: str, params: AntennaParameters, metadata: Optional[dict] = None) -> dict:
    """Convert AntennaParameters to database record format."""
    return {
        "instance_id": instance_id,
        "geometry_length": params.geometry.length,
        "geometry_width": params.geometry.width,
        "geometry_height": params.geometry.height,
        "geometry_feed_x": params.geometry.feed_x,
        "geometry_feed_y": params.geometry.feed_y,
        "substrate_type": params.substrate.substrate_type.value,
        "substrate_permittivity": params.substrate.relative_permittivity,
        "substrate_loss_tangent": params.substrate.loss_tangent,
        "substrate_thickness": params.substrate.thickness,
        "feed_type": params.feed_type.value,
        "frequency_band": params.frequency_band.value,
        "frequency_min": params.frequency_range[0],
        "frequency_max": params.frequency_range[1],
        "instance_metadata": metadata or {},
    }


def db_to_antenna_params(instance: AntennaInstance) -> AntennaParameters:
    """Convert database record to AntennaParameters."""
    from backend.core.models.schemas import AntennaGeometry, SubstrateProperties, SubstrateType, FeedType, FrequencyBand
    
    return AntennaParameters(
        geometry=AntennaGeometry(
            length=instance.geometry_length,
            width=instance.geometry_width,
            height=instance.geometry_height,
            feed_x=instance.geometry_feed_x,
            feed_y=instance.geometry_feed_y,
        ),
        substrate=SubstrateProperties(
            substrate_type=SubstrateType(instance.substrate_type),
            relative_permittivity=instance.substrate_permittivity,
            loss_tangent=instance.substrate_loss_tangent,
            thickness=instance.substrate_thickness,
        ),
        feed_type=FeedType(instance.feed_type),
        frequency_band=FrequencyBand(instance.frequency_band),
        frequency_range=(instance.frequency_min, instance.frequency_max),
    )


@router.post("/", status_code=201)
async def create_antenna_instance(
    parameters: AntennaParameters,
    instance_id: Optional[str] = None,
    metadata: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """Create a new antenna instance."""
    try:
        # Generate instance ID if not provided
        if not instance_id:
            instance_id = f"ANT-{uuid.uuid4().hex[:8].upper()}"
        
        # Check if instance_id already exists
        existing = db.query(AntennaInstance).filter(
            AntennaInstance.instance_id == instance_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Antenna instance with ID '{instance_id}' already exists"
            )
        
        # Create database record
        db_data = antenna_params_to_db(instance_id, parameters, metadata)
        instance = AntennaInstance(**db_data)
        
        db.add(instance)
        db.commit()
        db.refresh(instance)
        
        return {
            "id": instance.id,
            "instance_id": instance.instance_id,
            "parameters": parameters.model_dump(),
            "created_at": instance.created_at.isoformat(),
            "metadata": instance.metadata,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create antenna instance: {str(e)}")


@router.get("/", response_model=List[dict])
async def list_antenna_instances(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all antenna instances."""
    try:
        instances = db.query(AntennaInstance).offset(skip).limit(limit).all()
        
        return [
            {
                "id": inst.id,
                "instance_id": inst.instance_id,
                "parameters": db_to_antenna_params(inst).model_dump(),
                "created_at": inst.created_at.isoformat(),
                "updated_at": inst.updated_at.isoformat() if inst.updated_at else None,
                "metadata": inst.instance_metadata,
            }
            for inst in instances
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list antenna instances: {str(e)}")


@router.get("/{instance_id}")
async def get_antenna_instance(
    instance_id: str,
    db: Session = Depends(get_db)
):
    """Get antenna instance by ID."""
    try:
        instance = db.query(AntennaInstance).filter(
            AntennaInstance.instance_id == instance_id
        ).first()
        
        if not instance:
            raise HTTPException(status_code=404, detail=f"Antenna instance '{instance_id}' not found")
        
        return {
            "id": instance.id,
            "instance_id": instance.instance_id,
            "parameters": db_to_antenna_params(instance).model_dump(),
            "created_at": instance.created_at.isoformat(),
            "updated_at": instance.updated_at.isoformat() if instance.updated_at else None,
            "metadata": instance.metadata,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get antenna instance: {str(e)}")


@router.put("/{instance_id}")
async def update_antenna_instance(
    instance_id: str,
    parameters: AntennaParameters,
    metadata: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """Update antenna instance."""
    try:
        instance = db.query(AntennaInstance).filter(
            AntennaInstance.instance_id == instance_id
        ).first()
        
        if not instance:
            raise HTTPException(status_code=404, detail=f"Antenna instance '{instance_id}' not found")
        
        # Update fields
        db_data = antenna_params_to_db(instance_id, parameters, metadata)
        for key, value in db_data.items():
            if key != "instance_id":  # Don't update instance_id
                setattr(instance, key, value)
        
        instance.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(instance)
        
        return {
            "id": instance.id,
            "instance_id": instance.instance_id,
            "parameters": db_to_antenna_params(instance).model_dump(),
            "updated_at": instance.updated_at.isoformat(),
            "metadata": instance.metadata,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update antenna instance: {str(e)}")


@router.delete("/{instance_id}", status_code=204)
async def delete_antenna_instance(
    instance_id: str,
    db: Session = Depends(get_db)
):
    """Delete antenna instance."""
    try:
        instance = db.query(AntennaInstance).filter(
            AntennaInstance.instance_id == instance_id
        ).first()
        
        if not instance:
            raise HTTPException(status_code=404, detail=f"Antenna instance '{instance_id}' not found")
        
        db.delete(instance)
        db.commit()
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete antenna instance: {str(e)}")
