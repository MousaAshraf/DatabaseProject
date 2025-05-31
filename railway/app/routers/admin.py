from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import SessionLocal
from utils.permissions import get_admin_user
from crud import user as user_crud
from schemas.user import UserResponse
from datetime import date
from db.models import Ticket

router = APIRouter(prefix="/admin-api", tags=["admin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get(
    "/users",
    response_model=list[UserResponse],
    dependencies=[Depends(get_admin_user)],
)
def get_users(db: Session = Depends(get_db)):
    return db.query(user_crud.User).all()


@router.get("/ticket_logs")
def get_ticket_logs(
    db: Session = Depends(get_db), dependencies=[Depends(get_admin_user)]
):
    return db.query(Ticket).all()


@router.post("/report/fare_summary")
def generate_fare_summary(
    start_date: date, end_date: date, db: Session = Depends(get_db)
):
    fares = (
        db.query(Ticket)
        .filter(Ticket.EntryTime >= start_date, Ticket.EntryTime <= end_date)
        .all()
    )

    total = sum(ticket.Fare for ticket in fares)
    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_fares": total,
        "ticket_count": len(fares),
    }


@router.post("/report/user_trips")
def generate_user_trips_report(user_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Ticket)
        .filter(Ticket.UserID == user_id)
        .order_by(Ticket.EntryTime.desc())
        .all()
    )
