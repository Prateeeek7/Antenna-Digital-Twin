"""WebSocket endpoints for Unity integration."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import json

from backend.ml_models.inference_service import InferenceService
from backend.core.models.schemas import AntennaParameters

router = APIRouter()

inference_service = InferenceService()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for Unity communication."""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from Unity
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            msg_type = message.get("type")
            
            if msg_type == "predict":
                # Get prediction
                params_dict = message.get("parameters")
                params = AntennaParameters(**params_dict)
                prediction = inference_service.predict(params)
                
                # Send prediction back
                await websocket.send_json({
                    "type": "prediction",
                    "data": prediction.model_dump()
                })
            
            elif msg_type == "update_parameters":
                # Parameter update from Unity
                # Echo back confirmation
                await websocket.send_json({
                    "type": "parameters_updated",
                    "status": "ok"
                })
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })



















