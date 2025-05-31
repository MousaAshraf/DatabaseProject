from sqlalchemy.orm import Session
from db.models import Payment, PaymentTransaction, PaymentAuditLog, Ticket
from schemas.payment import PaymentBase


def get_payment(db: Session, payment_id: str):
    return db.query(Payment).filter(Payment.id == payment_id).first()


def get_payments_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    return (
        db.query(Payment)
        .filter(Payment.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_payment(db: Session, payment: PaymentBase, user_id: str):
    db_payment = Payment(
        user_id=user_id,
        ticket_id=payment.ticket_id,
        amount=payment.amount,
        status="pending",
    )

    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment


def update_payment_status(db: Session, payment_id: str, status: str):
    db_payment = get_payment(db, payment_id)
    if not db_payment:
        return None

    old_status = db_payment.status
    db_payment.status = status

    # Create audit log
    db_audit = PaymentAuditLog(
        payment_id=payment_id,
        old_status=old_status,
        new_status=status,
        changed_by="system",
        change_reason="Status update",
    )

    db.add(db_audit)
    db.commit()
    db.refresh(db_payment)
    return db_payment


def process_paymob_payment(db: Session, payment_data: dict):
    # Create payment record
    db_payment = Payment(
        user_id=payment_data["user_id"],
        ticket_id=payment_data.get("ticket_id"),
        amount=payment_data["amount"],
        status="completed",
        payment_method=payment_data["payment_method"],
        gateway_reference=payment_data["gateway_reference"],
        payment_key=payment_data["payment_key"],
        amount_cents=payment_data["amount_cents"],
        currency="EGP",
    )

    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)

    # Create transaction record
    db_transaction = PaymentTransaction(
        payment_id=db_payment.id,
        gateway_reference=payment_data["gateway_reference"],
        payment_key=payment_data["payment_key"],
        amount_cents=payment_data["amount_cents"],
        payment_method=payment_data["payment_method"],
        callback_payload=payment_data.get("callback_payload"),
    )

    db.add(db_transaction)

    # Update ticket if applicable
    if payment_data.get("ticket_id"):
        db_ticket = (
            db.query(Ticket).filter(Ticket.id == payment_data["ticket_id"]).first()
        )
        if db_ticket:
            db_ticket.status = "paid"
            db_ticket.fare_paid = payment_data["amount"]

    db.commit()
    return db_payment
