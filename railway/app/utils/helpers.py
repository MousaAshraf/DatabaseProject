from datetime import date, timedelta


def calculate_end_date(start_date: date, plan_type: str) -> date:
    if plan_type == "monthly":
        return start_date + timedelta(days=30)
    elif plan_type == "quarterly":
        return start_date + timedelta(days=90)
    elif plan_type == "yearly":
        return start_date + timedelta(days=365)
    raise ValueError("Invalid subscription type")
