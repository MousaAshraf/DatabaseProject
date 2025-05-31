from sqlalchemy.orm import Session
from db.models import Ticket, Station
from schemas.ticket import TicketCreate, TicketUpdate
from core.security import generate_qr_code
from datetime import datetime, timedelta

import uuid


def get_ticket(db: Session, ticket_id: str):
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()


def get_tickets_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    return (
        db.query(Ticket)
        .filter(Ticket.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_ticket(db: Session, ticket_data: TicketCreate, user_id: str):
    # Fetch station objects
    start_station = (
        db.query(Station).filter(Station.id == ticket_data.start_station_id).first()
    )
    end_station = (
        db.query(Station).filter(Station.id == ticket_data.end_station_id).first()
    )
    if not start_station or not end_station:
        raise ValueError("Invalid station IDs")

    # Calculate stations_count
    stations_count = abs(end_station.order - start_station.order) + 1

    # Calculate fare
    if stations_count <= 9:
        fare = 8.00
    elif stations_count <= 16:
        fare = 10.00
    elif stations_count <= 23:
        fare = 15.00
    else:
        fare = 20.00

    # Check subscription (optional, adjust as needed)
    max_zone = max(getattr(start_station, "zone", 1), getattr(end_station, "zone", 1))
    has_subscription = db.execute(
        "SELECT COUNT(*) > 0 FROM subscriptions "
        "WHERE user_id = :user_id AND is_active = TRUE "
        "AND DATE('now') BETWEEN start_date AND end_date "
        "AND zone_coverage >= :max_zone",
        {"user_id": user_id, "max_zone": max_zone},
    ).scalar()

    # Generate QR code
    qr_data = f"metro:{user_id}:{start_station.id}:{end_station.id}"
    qr_code = generate_qr_code(qr_data)

    ticket = Ticket(
        user_id=user_id,
        qr_code=qr_code,
        start_station_id=start_station.id,
        end_station_id=end_station.id,
        stations_count=stations_count,
        fare_paid=0.00 if has_subscription else fare,
        status="paid" if has_subscription else "active",
        expires_at=datetime.now() + timedelta(hours=2),
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def update_ticket(db: Session, ticket_id: str, ticket_update: TicketUpdate):
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None

    if ticket_update.status:
        db_ticket.status = ticket_update.status
    if ticket_update.entry_time:
        db_ticket.entry_time = ticket_update.entry_time
    if ticket_update.exit_time:
        db_ticket.exit_time = ticket_update.exit_time

    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def scan_ticket(db: Session, ticket_id: str, station_id: str, scan_type: str):
    ticket = get_ticket(db, ticket_id)
    if not ticket:
        return None

    if scan_type == "entry":
        ticket.entry_time = datetime.now()
        ticket.status = "used_entry"
    elif scan_type == "exit":
        ticket.exit_time = datetime.now()
        ticket.status = "completed"

    db.commit()
    db.refresh(ticket)
    return ticket
