from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TicketBase(BaseModel):
    user_id: str
    start_station_id: str
    end_station_id: str


class TicketCreate(TicketBase):
    pass


class TicketResponse(BaseModel):
    id: str
    user_id: str
    start_station_id: str
    end_station_id: str
    qr_code: str
    stations_count: int
    fare_paid: float
    status: str
    created_at: Optional[datetime] = None
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    expires_at: datetime

    model_config = {
        "from_attributes": True,
    }


class TicketScan(BaseModel):
    ticket_id: str
    station_id: str
    scan_type: str


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
