from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.database import get_db
from db.models import User, Ticket
from typing import Optional
from schemas.ticket import TicketCreate, TicketResponse, TicketUpdate, TicketScan
from crud.ticket import get_ticket, get_tickets_by_user, create_ticket
from utils.permissions import get_current_user
from typing import List

router = APIRouter(prefix="/tickets", tags=["Tickets"])


# In routers/tickets.py
@router.post("/", response_model=TicketResponse)
def create_ticket_endpoint(
    ticket_data: TicketCreate,  # Changed parameter name
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_ticket(db=db, ticket_data=ticket_data, user_id=str(current_user.id))


# tickets_router.py
@router.get("/tickets")
async def filter_tickets(
    status: Optional[str] = None,
    date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
    if date:
        query = query.filter(func.date(Ticket.created_at) == date)
    return query.all()


@router.post("/tickets/validate")
async def validate_ticket(
    ticket_id: str, scan_type: str, station_id: str, db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    # Add QR & scan validation logic here
    return {
        "message": f"{scan_type.title()} scan validated for ticket {ticket_id} at station {station_id}"
    }


@router.get("/", response_model=List[TicketResponse])
def read_tickets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_tickets_by_user(db=db, user_id=current_user.id, skip=skip, limit=limit)


@router.get("/{ticket_id}", response_model=TicketResponse)
def read_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_ticket = get_ticket(db, ticket_id=ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if db_ticket.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db_ticket


@router.post("/scan")
def scan_ticket(
    scan: TicketScan,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can scan tickets")

    return scan_ticket(
        db=db,
        ticket_id=scan.ticket_id,
        station_id=scan.station_id,
        scan_type=scan.scan_type,
    )


@router.put("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: str,
    ticket: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_ticket = get_ticket(db, ticket_id=ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if db_ticket.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    return update_ticket(db=db, ticket_id=ticket_id, ticket_update=ticket)


@router.get("{ticket_id}/qr", response_model=str)
def get_ticket_qr_code(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_ticket = get_ticket(db, ticket_id=ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if db_ticket.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    return db_ticket.qr_code
