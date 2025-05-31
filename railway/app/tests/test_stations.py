def test_create_station(client, admin_auth_headers, test_line):
    station_data = {
        "name": "New Station",
        "line_id": str(test_line.id),
        "zone": 2,
        "station_order": 1,
    }
    response = client.post(
        "/stations/",
        json=station_data,
        headers=admin_auth_headers,
    )
    assert response.status_code == 201


def test_get_stations(client, test_stations):
    response = client.get("/stations/")
    assert response.status_code == 200
    stations = response.json()
    assert isinstance(stations, list)
    assert len(stations) > 0
    assert stations[0]["name"] == "Test Station"


def test_get_station(client, test_stations):
    response = client.get(f"/stations/{test_stations[0].id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Station"


def test_calculate_fare(client, test_stations):
    start_id = test_stations[0].id  # Now works with list
    end_id = test_stations[1].id
    response = client.get(f"/stations/calculate-fare/{start_id}/{end_id}")
    assert response.status_code == 200
    assert "fare" in response.json()
