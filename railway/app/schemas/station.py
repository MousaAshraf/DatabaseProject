from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StationBase(BaseModel):
    name: str
    zone: int
    station_order: int
    line_id: str


class StationResponse(StationBase):
    id: str
    is_active: bool
    created_at: datetime  # Keep as datetime but ensure proper serialization

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}  # Simple datetime handling


class LineResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    is_active: bool

    model_config = {
        "from_attributes": True,
    }


class FareResponse(BaseModel):
    start_station_id: str
    end_station_id: str
    fare: float
    currency: str
