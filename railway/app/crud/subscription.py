from sqlalchemy.orm import Session
from db.models import Subscription
from schemas.subscription import SubscriptionCreate, SubscriptionRenew
from datetime import date, timedelta


def get_subscription(db: Session, subscription_id: str):
    return db.query(Subscription).filter(Subscription.id == subscription_id).first()


def get_subscriptions_by_user(
    db: Session, user_id: str, skip: int = 0, limit: int = 100
):
    return (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_active_subscription(db: Session, user_id: str):
    today = date.today()
    return (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user_id,
            Subscription.is_active,
            Subscription.start_date <= today,
            Subscription.end_date >= today,
        )
        .first()
    )


def create_subscription(db: Session, subscription: SubscriptionCreate, user_id: str):
    start_date = date.today()

    if subscription.plan_type == "monthly":
        end_date = start_date + timedelta(days=30)
    elif subscription.plan_type == "quarterly":
        end_date = start_date + timedelta(days=90)
    elif subscription.plan_type == "yearly":
        end_date = start_date + timedelta(days=365)
    else:
        return None

    db_subscription = Subscription(
        user_id=user_id,
        plan_type=subscription.plan_type,
        zone_coverage=subscription.zone_coverage,
        start_date=start_date,
        end_date=end_date,
        is_active=True,
    )

    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription


def renew_subscription(db: Session, subscription_id: str, renewal: SubscriptionRenew):
    db_subscription = get_subscription(db, subscription_id)
    if not db_subscription:
        return None

    if renewal.plan_type:
        db_subscription.plan_type = renewal.plan_type
    if renewal.zone_coverage:
        db_subscription.zone_coverage = renewal.zone_coverage

    # Calculate new end date
    start_date = (
        db_subscription.end_date
        if db_subscription.end_date >= date.today()
        else date.today()
    )

    if db_subscription.plan_type == "monthly":
        end_date = start_date + timedelta(days=30)
    elif db_subscription.plan_type == "quarterly":
        end_date = start_date + timedelta(days=90)
    elif db_subscription.plan_type == "yearly":
        end_date = start_date + timedelta(days=365)

    db_subscription.start_date = start_date
    db_subscription.end_date = end_date
    db_subscription.is_active = True

    db.commit()
    db.refresh(db_subscription)
    return db_subscription


def cancel_subscription(db: Session, subscription_id: str):
    db_subscription = get_subscription(db, subscription_id)
    if not db_subscription:
        return None

    db_subscription.is_active = False
    db.commit()
    db.refresh(db_subscription)
    return db_subscription
