from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import User
from crud.station import (
    get_stations,
    create_station,
    get_lines,
    get_line,
    calculate_fare,
)
from dependencies import require_admin  # Adjust the import path as needed
from schemas.station import StationResponse, LineResponse, FareResponse, StationBase
from typing import List


router = APIRouter(prefix="/stations", tags=["Stations"])


@router.post("/", response_model=StationResponse, status_code=status.HTTP_201_CREATED)
def create_new_station(
    station: StationBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),  # Admin-only
):
    """
    Create a new station (Admin only)
    """
    try:
        return create_station(db=db, station=station)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[StationResponse])
def read_stations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    stations = get_stations(db=db, skip=skip, limit=limit)
    if not stations:
        raise HTTPException(status_code=404, detail="No stations found")
    return stations


@router.get("/{station_id}", response_model=StationResponse)
def read_station(station_id: str, db: Session = Depends(get_db)):
    station = get_stations(db, station_id=station_id)
    if station is None:
        raise HTTPException(status_code=404, detail="Station not found")
    return station


@router.get("/lines/", response_model=List[LineResponse])
def read_lines(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    lines = get_lines(db=db, skip=skip, limit=limit)
    if not lines:
        raise HTTPException(status_code=404, detail="No lines found")
    return lines


@router.get("/lines/{line_id}", response_model=LineResponse)
def read_line(line_id: str, db: Session = Depends(get_db)):
    line = get_line(db, line_id=line_id)
    if line is None:
        raise HTTPException(status_code=404, detail="Line not found")
    return line


@router.get(
    "/calculate-fare/{start_station_id}/{end_station_id}", response_model=FareResponse
)
def calculate_fare_route(
    start_station_id: str, end_station_id: str, db: Session = Depends(get_db)
):
    fare = calculate_fare(db, start_station_id, end_station_id)
    return {
        "start_station_id": start_station_id,
        "end_station_id": end_station_id,
        "fare": fare,
        "currency": "EGP",
    }


# In routers/stations.py
