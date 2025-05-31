from fastapi import status
from core.security import verify_password, create_access_token


def test_verify_password_hash():
    assert verify_password(
        "secret", "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    )


def test_create_access_token():
    token = create_access_token(data={"sub": "test"})
    assert isinstance(token, str)


def test_login(client, test_user):

    response = client.post(
        "/auth/",
        data={"username": test_user["username"], "password": test_user["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_invalid_credentials(client):
    response = client.post(
        "/auth/", data={"username": "nonexistent", "password": "wrong"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_read_current_user(client, user_auth_headers):
    response = client.get("/me", headers=user_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"].startswith("testuser")


def test_read_current_user_unauthenticated(client):
    response = client.get("/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
