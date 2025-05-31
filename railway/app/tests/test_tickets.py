from fastapi import status
from datetime import datetime, timedelta


def test_create_ticket(client, test_user, test_stations, user_auth_headers):
    ticket_data = {
        "start_station_id": str(test_stations[0].id),  # Now works with list
        "end_station_id": str(test_stations[1].id),
        "fare_paid": 5.0,
        "status": "active",
        "expires_at": str(datetime.now() + timedelta(hours=1)),
    }
    response = client.post(
        "/tickets/",
        json=ticket_data,
        headers=user_auth_headers,
    )
    assert response.status_code == 201


def test_get_tickets(
    client, test_user, user_auth_headers, create_ticket, test_stations
):
    # First create a test ticket using actual station IDs
    ticket = create_ticket(
        user_id=test_user["id"],
        start_station_id=str(test_stations[0].id),
        end_station_id=str(test_stations[1].id),
    )

    response = client.get("/tickets/", headers=user_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    tickets = response.json()
    assert isinstance(tickets, list)
    assert len(tickets) > 0
    assert tickets[0]["id"] == str(ticket.id)


def test_scan_ticket(client, test_ticket, admin_auth_headers):
    scan_data = {
        "ticket_id": str(test_ticket.id),
        "station_id": str(test_ticket.start_station_id),
        "scan_type": "entry",
        "device_id": "scanner-1",
    }
    response = client.post(
        "/tickets/scan",
        json=scan_data,
        headers=admin_auth_headers,
    )
    assert response.status_code == 200
