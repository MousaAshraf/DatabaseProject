from fastapi import status


def test_create_user(client):
    # Generate exactly 9 digits after +201
    response = client.post(
        "/users/",
        json={
            "firstname": "New",
            "lastname": "User",
            "username": "newuser",
            "phone": "+201007550200",
            "email": "new_user@example.com",
            "password": "Newpass123!",
        },
    )
    print("Response JSON:", response.json())
    assert response.status_code == status.HTTP_201_CREATED
    assert "id" in response.json()


def test_get_users(client, admin_auth_headers):
    response = client.get("/users/", headers=admin_auth_headers)
    assert response.status_code == 200


def test_update_user(client, test_user, user_auth_headers):
    update_data = {
        "firstname": "UpdatedName",
        "password": "NewSecurePassword123!",  # Correct field name
    }
    response = client.put(
        f"/users/{test_user['id']}",
        json=update_data,
        headers=user_auth_headers,
    )
    assert response.status_code == 200, f"Update failed: {response.text}"
    assert response.json()["firstname"] == "UpdatedName"


def test_get_user(client, test_user, user_auth_headers):
    # Note: test_user is a dictionary, so we access id with ["id"] not .id
    user_id = test_user["id"]
    response = client.get(f"/users/{user_id}", headers=user_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    user_data = response.json()
    assert user_data["id"] == user_id
    assert user_data["username"] == test_user["username"]
