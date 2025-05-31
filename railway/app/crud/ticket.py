from sqlalchemy.orm import Session
from sqlalchemy import text
from db.models import Ticket, Station
from schemas.ticket import TicketCreate, TicketUpdate
from datetime import datetime, timedelta
from fastapi import HTTPException
import logging


import qrcode
import json
from io import BytesIO
import base64


def generate_qr_code(data: dict) -> str:
    """Generate base64 encoded QR code from dictionary data"""
    json_data = json.dumps(data)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(json_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()


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


def calculate_fare(stations_count: int) -> float:
    if stations_count <= 9:
        return 8.00
    elif stations_count <= 16:
        return 10.00
    elif stations_count <= 23:
        return 15.00
    else:
        return 20.00


def create_ticket(db: Session, ticket_data: TicketCreate, user_id: str):
    try:
        start_station = (
            db.query(Station).filter(Station.id == ticket_data.start_station_id).first()
        )
        end_station = (
            db.query(Station).filter(Station.id == ticket_data.end_station_id).first()
        )

        if not start_station or not end_station:
            raise HTTPException(status_code=404, detail="Invalid station IDs")

        if not hasattr(start_station, "station_order") or not hasattr(
            end_station, "station_order"
        ):
            raise HTTPException(
                status_code=500, detail="Station 'order' attribute missing"
            )

        stations_count = (
            abs(end_station.station_order - start_station.station_order) + 1
        )
        fare = calculate_fare(stations_count)

        max_zone = max(
            getattr(start_station, "zone", 1), getattr(end_station, "zone", 1)
        )

        has_subscription = db.execute(
            text(
                "SELECT COUNT(*) > 0 FROM subscriptions "
                "WHERE user_id = :user_id AND is_active = TRUE "
                "AND CURDATE() BETWEEN start_date AND end_date "
                "AND zone_coverage >= :max_zone"
            ),
            {"user_id": user_id, "max_zone": max_zone},
        ).scalar()

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

    except Exception as e:
        logging.error(f"Ticket creation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def update_ticket(db: Session, ticket_id: str, ticket_update: TicketUpdate):
    ticket = get_ticket(db, ticket_id)
    if not ticket:
        return None

    for attr, value in ticket_update.dict(exclude_unset=True).items():
        setattr(ticket, attr, value)

    db.commit()
    db.refresh(ticket)
    return ticket


def scan_ticket(db: Session, ticket_id: str, station_id: str, scan_type: str):
    ticket = get_ticket(db, ticket_id)
    if not ticket:
        return None

    now = datetime.now()

    if scan_type == "entry":
        ticket.entry_time = now
        ticket.status = "used_entry"
    elif scan_type == "exit":
        ticket.exit_time = now
        ticket.status = "completed"

    db.commit()
    db.refresh(ticket)
    return ticket
