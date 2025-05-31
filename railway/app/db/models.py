from sqlalchemy import (
    Column,
    String,
    Boolean,
    TIMESTAMP,
    Integer,
    ForeignKey,
    Enum,
    DECIMAL,
    Date,
    JSON,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    firstname = Column(String(50), nullable=False)
    lastname = Column(String(50), nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    email = Column(String(100), unique=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    last_password_hash_change = Column(TIMESTAMP)
    failed_login_attempts = Column(Integer, default=0)
    account_locked = Column(Boolean, default=False)

    # Relationships
    tickets = relationship("Ticket", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    payments = relationship("Payment", back_populates="user")

    def __str__(self):
        return self.username


class Line(Base):
    __tablename__ = "line"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    stations = relationship("Station", back_populates="line")

    def __str__(self):
        return self.name


class Station(Base):
    __tablename__ = "stations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    zone = Column(Integer, nullable=False, default=1)
    station_order = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    line_id = Column(String(36), ForeignKey("line.id"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    line = relationship("Line", back_populates="stations")
    start_tickets = relationship(
        "Ticket",
        foreign_keys="[Ticket.start_station_id]",
        back_populates="start_station",
    )
    end_tickets = relationship(
        "Ticket", foreign_keys="[Ticket.end_station_id]", back_populates="end_station"
    )
    scan_logs = relationship("ScanLog", back_populates="station")

    def __str__(self):
        return self.name


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    plan_type = Column(Enum("monthly", "quarterly", "yearly"), nullable=False)
    zone_coverage = Column(Integer, nullable=False, default=6)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="subscriptions")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    qr_code = Column(String(255), unique=True, nullable=False)
    start_station_id = Column(String(36), ForeignKey("stations.id"), nullable=False)
    end_station_id = Column(String(36), ForeignKey("stations.id"), nullable=False)
    stations_count = Column(Integer, nullable=False)
    fare_paid = Column(DECIMAL(10, 2), default=0.00)
    status = Column(
        Enum("active", "used_entry", "completed", "expired", "paid"), default="active"
    )
    created_at = Column(TIMESTAMP, server_default=func.now())
    entry_time = Column(TIMESTAMP)
    exit_time = Column(TIMESTAMP)
    expires_at = Column(TIMESTAMP, nullable=False)

    # Relationships
    user = relationship("User", back_populates="tickets")
    start_station = relationship(
        "Station", foreign_keys=[start_station_id], back_populates="start_tickets"
    )
    end_station = relationship(
        "Station", foreign_keys=[end_station_id], back_populates="end_tickets"
    )
    payments = relationship("Payment", back_populates="ticket")
    scan_logs = relationship("ScanLog", back_populates="ticket")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    ticket_id = Column(String(36), ForeignKey("tickets.id"))
    amount = Column(DECIMAL(10, 2), nullable=False)
    balance = Column(DECIMAL(10, 2), default=0)
    status = Column(
        Enum("pending", "completed", "failed", "refunded"), default="pending"
    )
    transaction_id = Column(String(255), unique=True)
    payment_date = Column(TIMESTAMP, server_default=func.now())
    last_four_digits = Column(String(4))
    payment_gateway = Column(String(50))
    gateway_reference = Column(String(255))
    ip_address = Column(String(45))
    payment_method = Column(String(50))
    currency = Column(String(3), default="EGP")
    amount_cents = Column(Integer)
    payment_key = Column(String(255))
    gateway_response_code = Column(String(50))
    gateway_response_message = Column(String(255))

    # Relationships
    user = relationship("User", back_populates="payments")
    ticket = relationship("Ticket", back_populates="payments")
    payment_transaction = relationship(
        "PaymentTransaction", uselist=False, back_populates="payment"
    )
    audit_logs = relationship("PaymentAuditLog", back_populates="payment")


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    payment_id = Column(String(36), ForeignKey("payments.id"), nullable=False)
    gateway_reference = Column(String(255), nullable=False)
    payment_key = Column(String(255), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="EGP")
    payment_method = Column(String(50), nullable=False)
    card_type = Column(String(50))
    masked_pan = Column(String(20))
    token = Column(String(255))
    callback_payload = Column(JSON)

    # Relationships
    payment = relationship("Payment", back_populates="payment_transaction")


class PaymentAuditLog(Base):
    __tablename__ = "payment_audit_log"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    payment_id = Column(String(36), ForeignKey("payments.id"), nullable=False)
    old_status = Column(String(20))
    new_status = Column(String(20), nullable=False)
    changed_by = Column(String(36))
    change_reason = Column(String(255))
    changed_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    payment = relationship("Payment", back_populates="audit_logs")


class ScanLog(Base):
    __tablename__ = "scan_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    ticket_id = Column(String(36), ForeignKey("tickets.id"), nullable=False)
    station_id = Column(String(36), ForeignKey("stations.id"), nullable=False)
    scan_type = Column(Enum("entry", "exit"), nullable=False)
    scan_time = Column(TIMESTAMP, server_default=func.now())
    success = Column(Boolean, default=True)
    failure_reason = Column(String(255))
    device_id = Column(String(100))
    operator_id = Column(String(36))

    # Relationships
    ticket = relationship("Ticket", back_populates="scan_logs")
    station = relationship("Station", back_populates="scan_logs")


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    event_type = Column(String(50), nullable=False)
    description = Column(Text)
    ip_address = Column(String(45))
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    user = relationship("User")
