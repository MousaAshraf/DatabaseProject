from sqlalchemy.orm import Session


def calculate_fare(db: Session, entry_station_id: int, exit_station_id: int):
    """Execute the stored procedure for fare calculation"""
    db.execute(
        "CALL CalculateFare(:entry_id, :exit_id, @fare)",
        {"entry_id": entry_station_id, "exit_id": exit_station_id},
    )
    fare = db.execute("SELECT @fare").fetchone()[0]
    return fare
