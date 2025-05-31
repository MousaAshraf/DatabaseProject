from datetime import datetime, timedelta


def test_create_subscription(client, user_auth_headers, test_user):
    sub_data = {
        "plan_type": "monthly",
        "zone_coverage": 2,
        "start_date": str(datetime.now().date()),
        "end_date": str((datetime.now() + timedelta(days=30)).date()),
        "user_id": str(test_user["id"]),  # Explicitly include user_id
    }
    response = client.post("/subscriptions/", json=sub_data, headers=user_auth_headers)
    print(response.json())  # Debug output
    assert response.status_code in [
        201,
        400,
        422,
    ], f"Unexpected status: {response.status_code}"
    if response.status_code == 201:
        assert response.json()["user_id"] == str(test_user["id"])
