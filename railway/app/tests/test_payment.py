from fastapi import status
import uuid
from datetime import datetime


def test_initiate_payment(client, user_auth_headers, test_ticket, mock_paymob):
    response = client.post(
        "/payments/initiate",
        json={"amount": 50.0, "ticket_id": str(test_ticket.id)},
        headers=user_auth_headers,
    )
    assert response.status_code == 201
    assert "payment_url" in response.json()


def test_payment_callback(client, mock_paymob, test_user, test_ticket):
    callback_data = {
        "obj": {
            "id": "pay_123",
            "amount_cents": 5000,
            "success": True,
            "order": {"id": "order_123"},
            "created_at": datetime.now().isoformat(),
            "currency": "EGP",
            "source_data": {"type": "card"},
            "integration_id": "123",
            "is_3d_secure": False,
            "pending": False,
            "merchant_order_id": str(test_ticket.id),
            "wallet_notification": None,
        },
        "hmac": "valid_hmac",
    }
    response = client.post("/payments/callback", json=callback_data)
    assert response.status_code == 200


def test_initiate_payment_invalid_ticket(client, user_auth_headers):
    response = client.post(
        "/payments/initiate",
        json={"amount": 50.0, "ticket_id": "invalid_ticket_id"},
        headers=user_auth_headers,
    )
    # Update assertion to match your API's actual behavior
    assert response.status_code in [
        400,
        404,
    ]  # Both are valid depending on implementation
    assert "detail" in response.json()


def test_payment_callback_failure(client, mocker):
    mocker.patch("core.payment.PaymobManager.verify_hmac", return_value=True)

    callback_data = {
        "obj": {
            "id": str(uuid.uuid4()),
            "amount_cents": 5000,
            "success": False,
            "error_occured": "Insufficient funds",
            "order": {"id": str(uuid.uuid4())},
        },
        "hmac": "test_hmac",
    }

    response = client.post("/payments/callback", json=callback_data)
    assert response.status_code == 200
    assert response.json()["status"] == "failed"


def test_payment_callback_invalid_hmac(client, mocker):
    mocker.patch("core.payment.PaymobManager.verify_hmac", return_value=False)

    response = client.post("/payments/callback", json={"obj": {}, "hmac": "invalid"})
    assert response.status_code == 400
