from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import User
from crud.subscription import (
    get_active_subscription,
    get_subscriptions_by_user,
    get_subscription,
)

from schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionRenew,
)

from utils.permissions import get_current_user
from typing import List

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post("/", response_model=SubscriptionResponse)
def create_subscription(
    subscription: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check if user already has an active subscription
    active_sub = get_active_subscription(db, current_user.id)
    if active_sub:
        raise HTTPException(
            status_code=400, detail="User already has an active subscription"
        )

    return create_subscription(
        db=db, subscription=subscription, user_id=current_user.id
    )


@router.get("/", response_model=List[SubscriptionResponse])
def read_subscriptions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_subscriptions_by_user(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )


@router.get("/active", response_model=SubscriptionResponse)
def read_active_subscription(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    subscription = get_active_subscription(db, current_user.id)
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    return subscription


@router.post("/{subscription_id}/renew", response_model=SubscriptionResponse)
def renew_subscription(
    subscription_id: str,
    renewal: SubscriptionRenew,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_subscription = get_subscription(db, subscription_id)
    if not db_subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if db_subscription.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    return renew_subscription(db=db, subscription_id=subscription_id, renewal=renewal)


@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponse)
def cancel_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_subscription = get_subscription(db, subscription_id)
    if not db_subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if db_subscription.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    return cancel_subscription(db=db, subscription_id=subscription_id)
