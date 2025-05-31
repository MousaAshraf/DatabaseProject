from sqlalchemy.orm import Session
from db.models import Station, Line
import uuid


def create_station(db: Session, station: Station) -> Station:
    db_station = Station(
        id=str(uuid.uuid4()),
        name=station.name,
        zone=station.zone,
        station_order=station.station_order,
        line_id=station.line_id,
        is_active=True,
    )
    db.add(db_station)
    db.commit()
    db.refresh(db_station)
    return db_station


def get_station(db: Session, station_id: str):
    return db.query(Station).filter(Station.id == station_id).first()


def get_stations(db: Session, skip: int = 0, limit: int = 100, station_id: str = None):
    if station_id:
        return db.query(Station).filter(Station.id == station_id).first()
    return db.query(Station).offset(skip).limit(limit).all()


def get_stations_by_line(db: Session, line_id: str):
    return db.query(Station).filter(Station.line_id == line_id).all()


def get_lines(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Line).offset(skip).limit(limit).all()


def get_line(db: Session, line_id: str):
    return db.query(Line).filter(Line.id == line_id).first()


def calculate_fare(db: Session, start_station_id: str, end_station_id: str):
    start_station = get_station(db, start_station_id)
    end_station = get_station(db, end_station_id)

    if not start_station or not end_station:
        return None

    station_count = abs(start_station.station_order - end_station.station_order) + 1

    if station_count <= 9:
        return 8.00
    elif station_count <= 16:
        return 10.00
    elif station_count <= 23:
        return 15.00
    else:
        return 20.00
