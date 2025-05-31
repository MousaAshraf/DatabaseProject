import requests
from fastapi import HTTPException, status
from typing import Dict
from .config import get_settings
import hashlib

settings = get_settings()


class PaymobManager:
    def __init__(self):
        self.config = {
            "api_key": settings.paymob_api_key,
            "merchant_id": settings.paymob_merchant_id,
            "iframe_id": settings.paymob_iframe_id,
            "integration_id": settings.paymob_integration_id,
            "hmac_secret": settings.paymob_hmac_secret,
        }
        self.auth_token = None

    def authenticate(self) -> str:
        url = "https://accept.paymob.com/api/auth/tokens"  # Corrected URL
        payload = {"api_key": self.config["api_key"]}

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            self.auth_token = response.json().get("token")
            if not self.auth_token:
                raise ValueError("No token received from Paymob")
            return self.auth_token
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Paymob authentication failed: {str(e)}",
            )

    def create_payment_order(
        self, amount_cents: int, user_id: str, ticket_id: str
    ) -> Dict:
        if not self.auth_token:
            self.authenticate()

        url = "https://accept.paymobsolutions.com/api/ecommerce/orders"
        items = [
            {
                "name": "Metro Ticket",
                "amount_cents": amount_cents,
                "description": f"Ticket {ticket_id} for user {user_id}",
                "quantity": "1",
            }
        ]

        payload = {
            "auth_token": self.auth_token,
            "delivery_needed": "false",
            "merchant_id": self.config["merchant_id"],
            "amount_cents": amount_cents,
            "currency": "EGP",
            "items": items,
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Paymob order creation failed: {str(e)}",
            )

    def get_payment_key(
        self, order_id: str, amount_cents: int, user_id: str, ticket_id: str
    ) -> Dict:
        if not self.auth_token:
            self.authenticate()

        url = "https://accept.paymobsolutions.com/api/acceptance/payment_keys"

        billing_data = {
            "first_name": "Metro",
            "last_name": "User",
            "email": "user@cairometro.com",
            "phone_number": "+201234567890",
            "city": "Cairo",
            "country": "Egypt",
        }

        payload = {
            "auth_token": self.auth_token,
            "amount_cents": amount_cents,
            "expiration": 3600,
            "order_id": order_id,
            "billing_data": billing_data,
            "currency": "EGP",
            "integration_id": self.config["integration_id"],
            "lock_order_when_paid": "false",
            "merchant_id": self.config["merchant_id"],
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Paymob payment key request failed: {str(e)}",
            )

    # Update the authenticate method

    # Update HMAC verification
    def verify_hmac(self, request_data: Dict, received_hmac: str) -> bool:
        # Paymob's required order of fields for HMAC calculation
        required_fields = [
            str(request_data.get("amount_cents", "")),
            str(request_data.get("created_at", "")),
            str(request_data.get("currency", "")),
            str(request_data.get("error_occured", "")),
            str(request_data.get("has_parent_transaction", "")),
            str(request_data.get("id", "")),
            str(request_data.get("integration_id", "")),
            str(request_data.get("is_3d_secure", "")),
            str(request_data.get("is_auth", "")),
            str(request_data.get("is_capture", "")),
            str(request_data.get("is_refunded", "")),
            str(request_data.get("is_standalone_payment", "")),
            str(request_data.get("is_voided", "")),
            str(request_data.get("order", {}).get("id", "")),
            str(request_data.get("owner", "")),
            str(request_data.get("pending", "")),
            str(request_data.get("source_data", {}).get("pan", "")),
            str(request_data.get("source_data", {}).get("sub_type", "")),
            str(request_data.get("success", "")),
            str(request_data.get("terminal_id", "")),
            str(request_data.get("txn_response_code", "")),
        ]

        concatenated = "".join(required_fields)
        calculated_hmac = hashlib.sha512(
            self.config["hmac_secret"].encode() + concatenated.encode()
        ).hexdigest()

        return calculated_hmac == received_hmac
