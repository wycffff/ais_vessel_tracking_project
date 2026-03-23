from datetime import datetime
from typing import Any
from pydantic import BaseModel


class VesselStateOut(BaseModel):
    mmsi: int
    vessel_name: str | None = None
    call_sign: str | None = None
    imo: int | None = None
    vessel_type: int | None = None
    destination: str | None = None
    latest_event_time: datetime | None = None
    lat: float | None = None
    lon: float | None = None
    sog: float | None = None
    cog: float | None = None
    heading: float | None = None
    nav_stat: int | None = None

    model_config = {'from_attributes': True}


class VesselTrackOut(BaseModel):
    mmsi: int
    event_time: datetime
    lat: float
    lon: float
    sog: float | None = None
    cog: float | None = None
    heading: float | None = None
    nav_stat: int | None = None
    rot: float | None = None
    pos_acc: bool | None = None
    raim: bool | None = None
    source_topic: str

    model_config = {'from_attributes': True}


class PredictionPoint(BaseModel):
    timestamp: datetime
    lat: float
    lon: float


class VesselPredictionOut(BaseModel):
    mmsi: int
    based_on_points: int
    minutes_ahead: int
    current_lat: float
    current_lon: float
    predicted_lat: float
    predicted_lon: float
    predicted_timestamp: datetime
    method: str


class McpToolCallIn(BaseModel):
    tool_name: str
    params: dict[str, Any] = {}


class McpToolCallOut(BaseModel):
    tool_name: str
    status: str
    tool_response: Any
    meta: dict[str, Any] | None = None


class AgentQueryIn(BaseModel):
    query: str


class AgentQueryOut(BaseModel):
    user_query: str
    tool_used: str
    tool_params: dict[str, Any]
    tool_result: Any
    answer: str
    status: str
