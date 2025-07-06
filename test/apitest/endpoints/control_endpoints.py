"""
LED Control Endpoints
"""
from fastapi import APIRouter, HTTPException
from dataclass.api_models import (
    ChangeEffectRequest, DissolveTimeRequest, 
    SpeedPercentRequest, MasterBrightnessRequest, OSCApiResponse
)
from dataclass.osc_models import OSCRequest, OSCMessageType, OSCDataType
from services.osc_client import OSCClientContext, UDPOSCClient

router = APIRouter()

osc_client = OSCClientContext(UDPOSCClient())

@router.post("/change_effect", response_model=OSCApiResponse)
async def change_effect(request: ChangeEffectRequest):
    try:
        osc_request = OSCRequest()
        osc_request.set_address("/change_effect")
        osc_request.set_message_type(OSCMessageType.LED_CONTROL)
        osc_request.add_parameter("effect_id", request.effect_id, OSCDataType.INT, "Effect ID")
        
        response = await osc_client.send_message(osc_request)
        
        log_message = f"Effect changed to: {request.effect_id}"
        
        return OSCApiResponse(
            success=response.is_success(),
            message=log_message,
            data={
                "effect_id": request.effect_id,
                "osc_response": response.__dict__
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/set_dissolve_time", response_model=OSCApiResponse)
async def set_dissolve_time(request: DissolveTimeRequest):
    try:
        osc_request = OSCRequest()
        osc_request.set_address("/set_dissolve_time")
        osc_request.set_message_type(OSCMessageType.LED_CONTROL)
        osc_request.add_parameter("time_ms", request.time_ms, OSCDataType.INT, "Dissolve time in ms")
        
        response = await osc_client.send_message(osc_request)
        
        log_message = f"Dissolve time set to: {request.time_ms}ms"
        
        return OSCApiResponse(
            success=response.is_success(),
            message=log_message,
            data={
                "time_ms": request.time_ms,
                "osc_response": response.__dict__
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/set_speed_percent", response_model=OSCApiResponse)
async def set_speed_percent(request: SpeedPercentRequest):
   
    try:
        osc_request = OSCRequest()
        osc_request.set_address("/set_speed_percent")
        osc_request.set_message_type(OSCMessageType.LED_CONTROL)
        osc_request.add_parameter("percent", request.percent, OSCDataType.INT, "Speed percentage")
        
        response = await osc_client.send_message(osc_request)
        
        log_message = f"Animation speed set to: {request.percent}%"
        
        return OSCApiResponse(
            success=response.is_success(),
            message=log_message,
            data={
                "percent": request.percent,
                "osc_response": response.__dict__
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/master_brightness", response_model=OSCApiResponse)
async def master_brightness(request: MasterBrightnessRequest):
    try:
        osc_request = OSCRequest()
        osc_request.set_address("/master_brightness")
        osc_request.set_message_type(OSCMessageType.BRIGHTNESS)
        osc_request.add_parameter("brightness", request.brightness, OSCDataType.INT, "Master brightness")
        
        response = await osc_client.send_message(osc_request)
        
        log_message = f"Master brightness set to: {request.brightness}"
        
        return OSCApiResponse(
            success=response.is_success(),
            message=log_message,
            data={
                "brightness": request.brightness,
                "osc_response": response.__dict__
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 