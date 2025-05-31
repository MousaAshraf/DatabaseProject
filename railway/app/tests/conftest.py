import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from db.models import Ticket, Subscription, Line, Station
from main import app
from db.database import Base, get_db
from datetime import datetime, timedelta


# ---------------------------
# Phone validation constant
# ---------------------------
EGYPT_PHONE_REGEX = r"^\+20(10|11|12|15)[0-9]{8}$"


def generate_valid_phone():
    suffix = str(uuid.uuid4().int)[-8:]
    return f"+2010{suffix}"


# ---------------------------
# SQLite in-memory test DB
# ---------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------
# Auto-clean DB before/after
# ---------------------------
@pytest.fixture(autouse=True)
def cleanup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


# ---------------------------
# Fixtures for test users
# ---------------------------
@pytest.fixture
def test_admin(client):
    # First check if admin exists
    response = client.post(
        "/auth/",
        data={"username": "adminuser", "password": "AdminPass123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if response.status_code == 200:
        return response.json()

    # Create admin if doesn't exist
    admin_data = {
        "firstname": "Admin",
        "lastname": "User",
        "username": "adminuser",
        "email": "admin@example.com",
        "password": "AdminPass123!",
        "is_admin": True,
        "phone": "+201000000000",
    }
    response = client.post("/users/", json=admin_data)
    assert response.status_code == 201
    return response.json()
    

@pytest.fixture
def admin_auth_headers(client, test_admin):
    response = client.post(
        "/auth/",
        data={
            "username": "adminuser",
            "password": "AdminPass123!",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    @pytest.fixture
    def auth_headers(test_admin):
        return {"Authorization": f"Bearer {test_admin.get_token()}"}

    def test_something(client, auth_headers):
        response = client.get("/endpoint", headers=auth_headers)


@pytest.fixture
def test_user(client):
    phone = generate_valid_phone()
    user_data = {
        "firstname": "Test",
        "lastname": "User",
        "username": "testusers",
        "phone": phone,
        "email": "test_users@example.com",
        "password": "Testpass123!",  # Ensure password is included
    }
    response = client.post("/users/", json=user_data)
    assert response.status_code == 201, response.text
    user = response.json()
    user["password"] = "Testpass123!"  # Add password to returned dict
    return user


@pytest.fixture
def user_auth_headers(client, test_user):
    response = client.post(
        "/auth/",
        data={
            "username": test_user["username"],
            "password": test_user["password"],  # Use the stored password
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


# conftest.py


@pytest.fixture
def create_subscription(db):
    def _create_subscription(
        user_id: str,  # Changed from id to user_id to match model
        plan_type: str = "monthly",
        zone_coverage: int = 2,
        start_date: datetime = datetime.now(),
        end_date: datetime = datetime.now() + timedelta(days=30),
    ):
        subscription = Subscription(
            user_id=user_id,
            plan_type=plan_type,
            zone_coverage=zone_coverage,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        return subscription

    return _create_subscription


@pytest.fixture
def create_line(db):
    def _create_line(name: str = "Line 1"):
        line = Line(name=name)
        db.add(line)
        db.commit()
        db.refresh(line)
        return line

    return _create_line


# Update test_station_data fixture:
@pytest.fixture
def test_station_data():
    return {
        "name": "Central Station",
        "zone": 1,  # SINGULAR 'zone'
        "station_order": 1,
        "line_id": "line-1-uuid",
    }


# In conftest.py
@pytest.fixture
def test_ticket(db, test_user, test_stations):
    ticket = Ticket(
        user_id=test_user["id"],
        start_station_id=test_stations[0].id,
        end_station_id=test_stations[1].id,
        stations_count=5,  # Add this
        fare_paid=5.0,
        status="active",
        qr_code=f"qr_{uuid.uuid4()}",
        expires_at=datetime.now() + timedelta(hours=1),
    )
    db.add(ticket)
    db.commit()
    return ticket


@pytest.fixture
def create_ticket(db, test_user, test_stations):
    def _create_ticket(
        user_id: str = None,
        start_station_id: str = None,
        end_station_id: str = None,
        fare_paid: float = 5.0,
        status: str = "active",
    ):
        if not user_id:
            user_id = test_user["id"]

        if not start_station_id or not end_station_id:
            station1 = test_stations(name="Station A")
            station2 = test_stations(name="Station B")
            start_station_id = station1.id
            end_station_id = station2.id

        ticket = Ticket(
            user_id=user_id,
            start_station_id=start_station_id,
            end_station_id=end_station_id,
            fare_paid=fare_paid,
            status=status,
            qr_code=f"qr_{uuid.uuid4()}",
            expires_at=datetime.now() + timedelta(hours=1),
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket

    return _create_ticket


@pytest.fixture
def mock_paymob(mocker):
    # Mock all PaymobManager methods
    mocker.patch("core.payment.PaymobManager.authenticate")
    mocker.patch("core.payment.PaymobManager.create_payment_order")
    mocker.patch("core.payment.PaymobManager.get_payment_key")
    mocker.patch("core.payment.PaymobManager.verify_hmac", return_value=True)


@pytest.fixture
def test_line(db):
    line = Line(name="Test Line")
    db.add(line)
    db.commit()
    db.refresh(line)
    return line


@pytest.fixture
def test_stations(db, test_line):
    station1 = Station(
        name="Test Station",
        line_id=test_line.id,
        zone=1,
        station_order=1,
    )
    station2 = Station(
        name="Station B",
        line_id=test_line.id,
        zone=1,
        station_order=2,
    )
    db.add(station1)
    db.add(station2)
    db.commit()
    db.refresh(station1)
    db.refresh(station2)
    return [station1, station2]  # Explicitly return a list
