from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PaymentBase(BaseModel):
    amount: float
    ticket_id: Optional[str] = None


class PaymentResponse(BaseModel):
    id: str
    user_id: str
    ticket_id: Optional[str]
    amount: float
    status: str
    payment_date: datetime
    payment_method: Optional[str]
    gateway_reference: Optional[str]

    model_config = {
        "from_attributes": True,
    }


class PaymentStatus(BaseModel):
    payment_id: str
    status: str
    amount: float
    payment_date: datetime
    ticket_id: Optional[str]
    ticket_status: Optional[str]


class PaymentCallback(BaseModel):
    obj: dict
    hmac: str
