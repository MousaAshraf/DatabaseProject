from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
import uuid
import json
from io import BytesIO
from PIL import Image
from pyzbar.pyzbar import decode
import qrcode
from schemas.ticket import TicketCreate, TicketResponse, TicketUpdate
from db.database import get_db
from db.models import Ticket  # Your ORM model here

# Import or implement your QR code generation logic here

router = APIRouter(prefix="/tickets", tags=["tickets"])


# Example placeholder function to generate QR code string (replace with your QR lib)
def generate_qr_code(data: str) -> str:
    # e.g. return a base64 PNG or URL
    return f"QR({data})"


@router.get("/tickets/{ticket_id}/qr")
async def get_ticket_qr(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    qr_content = f"id:{ticket.id};user:{ticket.user_id};from:{ticket.start_station_id};to:{ticket.end_station_id}"
    qr_img = qrcode.make(qr_content)
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@router.post("/scan-qr/")
async def scan_qr(file: UploadFile = File(...)):
    img_bytes = await file.read()
    try:
        img = Image.open(BytesIO(img_bytes))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    decoded_objs = decode(img)
    if not decoded_objs:
        raise HTTPException(status_code=404, detail="No QR code found")

    qr_data = decoded_objs[0].data.decode("utf-8")

    try:
        ticket_info = json.loads(qr_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid QR code content")

    return {"ticket_info": ticket_info}


@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(ticket_in: TicketCreate, db: Session = Depends(get_db)):
    # Validate and create your ticket logic
    ticket_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=2)  # Example expiration

    qr_content = f"id:{ticket_id};user:{ticket_in.user_id};from:{ticket_in.start_station_id};to:{ticket_in.end_station_id}"
    qr_code_str = generate_qr_code(qr_content)

    ticket = Ticket(
        id=ticket_id,
        user_id=ticket_in.user_id,
        start_station_id=ticket_in.start_station_id,
        end_station_id=ticket_in.end_station_id,
        qr_code=qr_code_str,
        stations_count=5,  # calculate properly
        fare_paid=10.0,  # calculate properly
        status="active",
        created_at=datetime.utcnow(),
        expires_at=expires_at,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return TicketResponse.model_validate(ticket)


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return TicketResponse.model_validate(ticket)


@router.get("/", response_model=List[TicketResponse])
async def list_tickets(db: Session = Depends(get_db)):
    tickets = db.query(Ticket).all()
    return [TicketResponse.model_validate(t) for t in tickets]


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str, ticket_update: TicketUpdate, db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    update_data = ticket_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ticket, key, value)

    db.commit()
    db.refresh(ticket)
    return TicketResponse.model_validate(ticket)
