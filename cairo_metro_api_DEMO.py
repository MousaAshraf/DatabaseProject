from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import mysql.connector
from mysql.connector import Error
import hashlib
import jwt
import requests
import json
from datetime import datetime, timedelta
import os
from decimal import Decimal

# FastAPI app initialization
app = FastAPI(title="Cairo Metro API", version="1.0.0")

# CORS middleware for Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = "your-secret-key-here"  # Change this in production
ALGORITHM = "HS256"

# Paymob Configuration
PAYMOB_API_KEY = "your-paymob-api-key"  # Replace with your Paymob API key
PAYMOB_INTEGRATION_ID = "your-integration-id"  # Replace with your integration ID
PAYMOB_IFRAME_ID = "your-iframe-id"  # Replace with your iframe ID

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'cairo_metro_simple',
    'user': 'your-username',  # Replace with your DB username
    'password': 'your-password'  # Replace with your DB password
}

# Pydantic Models
class UserRegister(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    password: str

class UserLogin(BaseModel):
    phone: str
    password: str

class TicketPurchase(BaseModel):
    from_station_id: int
    to_station_id: int

class SubscriptionPurchase(BaseModel):
    plan_type: str  # 'monthly', 'quarterly', 'yearly'

class PaymentCallback(BaseModel):
    id: int
    pending: bool
    amount_cents: int
    success: bool
    is_auth: bool
    is_capture: bool
    is_standalone_payment: bool
    is_voided: bool
    is_refunded: bool
    is_3d_secure: bool
    integration_id: int
    profile_id: int
    has_parent_transaction: bool
    order: dict
    created_at: str
    transaction_processed_callback_at: Optional[str]
    currency: str
    source_data: dict
    api_source: str
    terminal_id: Optional[int]
    merchant_commission: int
    installment: Optional[str]
    discount_details: list
    is_void: bool
    is_refund: bool
    data: dict
    is_hidden: bool
    payment_key_claims: dict
    error_occured: bool
    is_live: bool
    other_endpoint_reference: Optional[str]
    refunded_amount_cents: int
    source_id: int
    is_captured: bool
    captured_amount: int
    merchant_staff_tag: Optional[str]
    updated_at: str
    is_settled: bool
    bill_balanced: bool
    is_bill: bool
    is_blocked: bool
    wallet_notification: Optional[dict]
    paid_amount_cents: int
    notify_user_done: bool
    merchant_order_id: Optional[str]
    wallet_issuer: Optional[str]
    blind_installment: Optional[str]
    voice_id: Optional[str]
    receipt_id: Optional[str]
    order_url: Optional[str]
    gateway_integration_pk: int
    delivery_needed: bool
    merchant: dict
    invoice_id: Optional[str]
    owner: int
    parent_transaction: Optional[dict]

# Database connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

# Authentication utilities
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Paymob utilities
def get_paymob_auth_token():
    """Get authentication token from Paymob"""
    url = "https://accept.paymob.com/api/auth/tokens"
    data = {"api_key": PAYMOB_API_KEY}
    
    response = requests.post(url, json=data)
    if response.status_code == 201:
        return response.json()["token"]
    else:
        raise HTTPException(status_code=500, detail="Failed to authenticate with Paymob")

def create_paymob_order(auth_token: str, amount_cents: int, currency: str = "EGP"):
    """Create order in Paymob"""
    url = "https://accept.paymob.com/api/ecommerce/orders"
    data = {
        "auth_token": auth_token,
        "delivery_needed": "false",
        "amount_cents": amount_cents,
        "currency": currency,
        "items": []
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 201:
        return response.json()
    else:
        raise HTTPException(status_code=500, detail="Failed to create Paymob order")

def get_payment_key(auth_token: str, order_id: int, amount_cents: int, user_data: dict):
    """Get payment key from Paymob"""
    url = "https://accept.paymob.com/api/acceptance/payment_keys"
    data = {
        "auth_token": auth_token,
        "amount_cents": amount_cents,
        "expiration": 3600,
        "order_id": order_id,
        "billing_data": {
            "apartment": "803",
            "email": user_data.get("email", "test@example.com"),
            "floor": "42",
            "first_name": user_data.get("name", "N/A").split()[0],
            "street": "Ethan Land",
            "building": "8028",
            "phone_number": user_data.get("phone", "+20100000000"),
            "shipping_method": "PKG",
            "postal_code": "01898",
            "city": "Cairo",
            "country": "EG",
            "last_name": user_data.get("name", "N/A").split()[-1] if len(user_data.get("name", "N/A").split()) > 1 else "N/A",
            "state": "Cairo"
        },
        "currency": "EGP",
        "integration_id": PAYMOB_INTEGRATION_ID
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 201:
        return response.json()["token"]
    else:
        raise HTTPException(status_code=500, detail="Failed to get payment key")

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Cairo Metro API is running"}

@app.post("/auth/register")
async def register(user_data: UserRegister):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE phone = %s", (user_data.phone,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Phone number already registered")
        
        # Hash password and insert user
        hashed_password = hash_password(user_data.password)
        cursor.execute(
            "INSERT INTO users (name, phone, email, password) VALUES (%s, %s, %s, %s)",
            (user_data.name, user_data.phone, user_data.email, hashed_password)
        )
        connection.commit()
        
        # Get user ID
        user_id = cursor.lastrowid
        
        # Create access token
        access_token = create_access_token({"user_id": user_id})
        
        return {
            "message": "User registered successfully",
            "access_token": access_token,
            "user_id": user_id
        }
    
    except Error as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        connection.close()

@app.post("/auth/login")
async def login(login_data: UserLogin):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("SELECT id, password, name, is_admin FROM users WHERE phone = %s", (login_data.phone,))
        user = cursor.fetchone()
        
        if not user or not verify_password(login_data.password, user[1]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        access_token = create_access_token({"user_id": user[0]})
        
        return {
            "access_token": access_token,
            "user_id": user[0],
            "name": user[2],
            "is_admin": bool(user[3])
        }
    
    finally:
        cursor.close()
        connection.close()

@app.get("/stations")
async def get_stations():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            SELECT s.id, s.name, s.station_order, l.name as line_name, l.color 
            FROM stations s 
            JOIN lines l ON s.line_id = l.id 
            ORDER BY l.id, s.station_order
        """)
        stations = cursor.fetchall()
        
        return [
            {
                "id": station[0],
                "name": station[1],
                "station_order": station[2],
                "line_name": station[3],
                "line_color": station[4]
            }
            for station in stations
        ]
    
    finally:
        cursor.close()
        connection.close()

@app.get("/lines")
async def get_lines():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("SELECT id, name, color FROM lines ORDER BY id")
        lines = cursor.fetchall()
        
        return [
            {
                "id": line[0],
                "name": line[1],
                "color": line[2]
            }
            for line in lines
        ]
    
    finally:
        cursor.close()
        connection.close()

@app.post("/calculate-fare")
async def calculate_fare(ticket_data: TicketPurchase):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("SELECT calculate_fare_between_stations(%s, %s)", 
                      (ticket_data.from_station_id, ticket_data.to_station_id))
        fare = cursor.fetchone()[0]
        
        if fare == 0:
            raise HTTPException(status_code=400, detail="Invalid route - stations must be on the same line")
        
        # Get station names
        cursor.execute("""
            SELECT s1.name, s2.name, l1.name, l2.name
            FROM stations s1 
            JOIN stations s2 ON s2.id = %s
            JOIN lines l1 ON s1.line_id = l1.id
            JOIN lines l2 ON s2.line_id = l2.id
            WHERE s1.id = %s
        """, (ticket_data.to_station_id, ticket_data.from_station_id))
        
        station_info = cursor.fetchone()
        
        return {
            "from_station": station_info[0],
            "to_station": station_info[1],
            "from_line": station_info[2],
            "to_line": station_info[3],
            "fare": float(fare)
        }
    
    finally:
        cursor.close()
        connection.close()

@app.post("/purchase-ticket")
async def purchase_ticket(ticket_data: TicketPurchase, user_id: int = Depends(get_current_user)):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Calculate fare
        cursor.execute("SELECT calculate_fare_between_stations(%s, %s)", 
                      (ticket_data.from_station_id, ticket_data.to_station_id))
        fare = cursor.fetchone()[0]
        
        if fare == 0:
            raise HTTPException(status_code=400, detail="Invalid route")
        
        # Check if user has active subscription
        cursor.execute("SELECT has_active_subscription(%s)", (user_id,))
        has_subscription = cursor.fetchone()[0]
        
        if has_subscription:
            # User has subscription, create ticket without payment
            cursor.execute("""
                INSERT INTO tickets (user_id, from_station_id, to_station_id, fare, expires_at) 
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, ticket_data.from_station_id, ticket_data.to_station_id, 
                  fare, datetime.now() + timedelta(hours=2)))
            
            connection.commit()
            ticket_id = cursor.lastrowid
            
            return {
                "message": "Ticket created successfully (subscription user)",
                "ticket_id": ticket_id,
                "fare": float(fare),
                "payment_required": False
            }
        else:
            # User needs to pay, get user data for Paymob
            cursor.execute("SELECT name, phone, email FROM users WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                raise HTTPException(status_code=404, detail="User not found")
            
            user_info = {
                "name": user_data[0],
                "phone": user_data[1],
                "email": user_data[2] or f"user{user_id}@cairometro.com"
            }
            
            # Create ticket first
            cursor.execute("""
                INSERT INTO tickets (user_id, from_station_id, to_station_id, fare, expires_at) 
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, ticket_data.from_station_id, ticket_data.to_station_id, 
                  fare, datetime.now() + timedelta(hours=2)))
            
            ticket_id = cursor.lastrowid
            
            # Create payment record
            cursor.execute("""
                INSERT INTO payments (user_id, ticket_id, amount, status) 
                VALUES (%s, %s, %s, 'pending')
            """, (user_id, ticket_id, fare))
            
            payment_id = cursor.lastrowid
            connection.commit()
            
            # Initialize Paymob payment
            try:
                auth_token = get_paymob_auth_token()
                amount_cents = int(float(fare) * 100)  # Convert to cents
                
                order = create_paymob_order(auth_token, amount_cents)
                payment_key = get_payment_key(auth_token, order["id"], amount_cents, user_info)
                
                payment_url = f"https://accept.paymob.com/api/acceptance/iframes/{PAYMOB_IFRAME_ID}?payment_token={payment_key}"
                
                return {
                    "message": "Ticket created, payment required",
                    "ticket_id": ticket_id,
                    "payment_id": payment_id,
                    "fare": float(fare),
                    "payment_required": True,
                    "payment_url": payment_url,
                    "payment_token": payment_key
                }
            
            except Exception as e:
                # Rollback ticket creation if payment initialization fails
                cursor.execute("DELETE FROM tickets WHERE id = %s", (ticket_id,))
                cursor.execute("DELETE FROM payments WHERE id = %s", (payment_id,))
                connection.commit()
                raise HTTPException(status_code=500, detail=f"Payment initialization failed: {str(e)}")
    
    except Error as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        connection.close()

@app.post("/purchase-subscription")
async def purchase_subscription(sub_data: SubscriptionPurchase, user_id: int = Depends(get_current_user)):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Define subscription prices and durations
        subscription_plans = {
            "monthly": {"price": 180.00, "months": 1},
            "quarterly": {"price": 500.00, "months": 3},
            "yearly": {"price": 1800.00, "months": 12}
        }
        
        if sub_data.plan_type not in subscription_plans:
            raise HTTPException(status_code=400, detail="Invalid subscription plan")
        
        plan = subscription_plans[sub_data.plan_type]
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=30 * plan["months"])
        
        # Get user data for Paymob
        cursor.execute("SELECT name, phone, email FROM users WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_info = {
            "name": user_data[0],
            "phone": user_data[1],
            "email": user_data[2] or f"user{user_id}@cairometro.com"
        }
        
        # Create subscription
        cursor.execute("""
            INSERT INTO subscriptions (user_id, plan_type, start_date, end_date, price, is_active) 
            VALUES (%s, %s, %s, %s, %s, FALSE)
        """, (user_id, sub_data.plan_type, start_date, end_date, plan["price"]))
        
        subscription_id = cursor.lastrowid
        
        # Create payment record
        cursor.execute("""
            INSERT INTO payments (user_id, subscription_id, amount, status) 
            VALUES (%s, %s, %s, 'pending')
        """, (user_id, subscription_id, plan["price"]))
        
        payment_id = cursor.lastrowid
        connection.commit()
        
        # Initialize Paymob payment
        try:
            auth_token = get_paymob_auth_token()
            amount_cents = int(plan["price"] * 100)  # Convert to cents
            
            order = create_paymob_order(auth_token, amount_cents)
            payment_key = get_payment_key(auth_token, order["id"], amount_cents, user_info)
            
            payment_url = f"https://accept.paymob.com/api/acceptance/iframes/{PAYMOB_IFRAME_ID}?payment_token={payment_key}"
            
            return {
                "message": "Subscription created, payment required",
                "subscription_id": subscription_id,
                "payment_id": payment_id,
                "plan_type": sub_data.plan_type,
                "price": plan["price"],
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "payment_url": payment_url,
                "payment_token": payment_key
            }
        
        except Exception as e:
            # Rollback subscription creation if payment initialization fails
            cursor.execute("DELETE FROM subscriptions WHERE id = %s", (subscription_id,))
            cursor.execute("DELETE FROM payments WHERE id = %s", (payment_id,))
            connection.commit()
            raise HTTPException(status_code=500, detail=f"Payment initialization failed: {str(e)}")
    
    except Error as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        connection.close()

@app.post("/payment-callback")
async def payment_callback(callback_data: dict):
    """Handle Paymob payment callback"""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        if callback_data.get("success") and callback_data.get("pending") == False:
            # Payment successful
            order_id = callback_data.get("order", {}).get("id")
            amount_cents = callback_data.get("amount_cents", 0)
            
            # Find the payment record
            cursor.execute("""
                SELECT p.id, p.user_id, p.ticket_id, p.subscription_id 
                FROM payments p 
                WHERE p.amount = %s AND p.status = 'pending'
                ORDER BY p.id DESC LIMIT 1
            """, (amount_cents / 100,))
            
            payment = cursor.fetchone()
            
            if payment:
                payment_id, user_id, ticket_id, subscription_id = payment
                
                # Update payment status
                cursor.execute("UPDATE payments SET status = 'completed' WHERE id = %s", (payment_id,))
                
                if ticket_id:
                    # Activate ticket
                    cursor.execute("UPDATE tickets SET status = 'active' WHERE id = %s", (ticket_id,))
                
                if subscription_id:
                    # Activate subscription
                    cursor.execute("UPDATE subscriptions SET is_active = TRUE WHERE id = %s", (subscription_id,))
                
                connection.commit()
                
                return {"message": "Payment processed successfully"}
        else:
            # Payment failed
            return {"message": "Payment failed"}
    
    except Error as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        connection.close()

@app.get("/user/tickets")
async def get_user_tickets(user_id: int = Depends(get_current_user)):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            SELECT t.id, s1.name as from_station, s2.name as to_station, 
                   t.fare, t.status, t.created_at, t.expires_at
            FROM tickets t
            JOIN stations s1 ON t.from_station_id = s1.id
            JOIN stations s2 ON t.to_station_id = s2.id
            WHERE t.user_id = %s
            ORDER BY t.created_at DESC
        """, (user_id,))
        
        tickets = cursor.fetchall()
        
        return [
            {
                "id": ticket[0],
                "from_station": ticket[1],
                "to_station": ticket[2],
                "fare": float(ticket[3]),
                "status": ticket[4],
                "created_at": ticket[5].isoformat() if ticket[5] else None,
                "expires_at": ticket[6].isoformat() if ticket[6] else None
            }
            for ticket in tickets
        ]
    
    finally:
        cursor.close()
        connection.close()

@app.get("/user/subscriptions")
async def get_user_subscriptions(user_id: int = Depends(get_current_user)):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            SELECT id, plan_type, start_date, end_date, price, is_active
            FROM subscriptions 
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        
        subscriptions = cursor.fetchall()
        
        return [
            {
                "id": sub[0],
                "plan_type": sub[1],
                "start_date": sub[2].isoformat() if sub[2] else None,
                "end_date": sub[3].isoformat() if sub[3] else None,
                "price": float(sub[4]),
                "is_active": bool(sub[5])
            }
            for sub in subscriptions
        ]
    
    finally:
        cursor.close()
        connection.close()

@app.get("/user/profile")
async def get_user_profile(user_id: int = Depends(get_current_user)):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            SELECT name, phone, email, is_admin, created_at,
                   has_active_subscription(%s) as has_active_sub
            FROM users 
            WHERE id = %s
        """, (user_id, user_id))
        
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": user_id,
            "name": user[0],
            "phone": user[1],
            "email": user[2],
            "is_admin": bool(user[3]),
            "created_at": user[4].isoformat() if user[4] else None,
            "has_active_subscription": bool(user[5])
        }
    
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)