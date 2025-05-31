from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
from datetime import datetime


class SubscriptionBase(BaseModel):
    type: str = Field(..., pattern="^(monthly|quarterly|yearly)$")
    zone_coverage: int = Field(..., ge=1, le=3)


class SubscriptionCreate(SubscriptionBase):
    user_id: int


class SubscriptionResponse(SubscriptionBase):
    subscription_id: int
    user_id: int
    start_date: date
    end_date: date
    status: str

    model_config = {
        "from_attributes": True,
    }


class SubscriptionRenew(BaseModel):
    plan_type: Optional[str] = None
    zone_coverage: Optional[int] = None
