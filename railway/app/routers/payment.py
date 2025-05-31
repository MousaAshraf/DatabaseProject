from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.payment import PaymentCallback, PaymentBase
from db.models import User
from crud.payment import process_paymob_payment
from core.payment import PaymobManager
from dependencies import get_current_user
from fastapi.responses import RedirectResponse


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/callback")
def payment_callback(callback_data: PaymentCallback, db: Session = Depends(get_db)):
    try:
        paymob_manager = PaymobManager()
        if not paymob_manager.verify_hmac(callback_data.obj, callback_data.hmac):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid HMAC signature"
            )

        if callback_data.obj.get("success"):
            payment_data = {
                "user_id": callback_data.obj.get("user_id"),
                "ticket_id": callback_data.obj.get("ticket_id"),
                "amount": callback_data.obj.get("amount") / 100,
                "payment_method": callback_data.obj.get("source_data", {}).get("type"),
                "gateway_reference": callback_data.obj.get("id"),
                "payment_key": callback_data.obj.get("payment_key"),
                "amount_cents": callback_data.obj.get("amount_cents"),
                "callback_payload": callback_data.obj,
            }
            payment = process_paymob_payment(db, payment_data)
            return {"status": "success", "payment_id": payment.id}
        else:
            return {
                "status": "failed",
                "reason": callback_data.obj.get("error_occured"),
            }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/initiate", status_code=201)
def initiate_payment(
    payment_req: PaymentBase,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        paymob_manager = PaymobManager()
        paymob_manager.authenticate()
        order = paymob_manager.create_payment_order(
            amount_cents=int(payment_req.amount * 100),
            user_id=str(current_user.id),
            ticket_id=payment_req.ticket_id,
        )
        payment_key = paymob_manager.get_payment_key(
            order_id=order["id"],
            amount_cents=int(payment_req.amount * 100),
            user_id=str(current_user.id),
            ticket_id=payment_req.ticket_id,
        )
        return {
            "payment_url": f"https://accept.paymobsolutions.com/api/acceptance/iframes/{paymob_manager.config['iframe_id']}?payment_token={payment_key['token']}",
            "payment_id": order["id"],
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/pay")
def redirect_to_paymob():
    payment_token = "your_payment_token_here"
    return RedirectResponse(
        f"https://accept.paymobsolutions.com/api/acceptance/post_pay?payment_token={payment_token}"
    )
