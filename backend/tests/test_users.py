def test_register_user(client):
    response = client.post(
        "/users/register",
        json={
            "email": "driver@example.com",
            "password": "hunter22",
            "full_name": "Dana Driver",
            "phone_number": "+15550000000",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "driver@example.com"
    assert body["full_name"] == "Dana Driver"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_email_is_rejected(client):
    payload = {
        "email": "driver@example.com",
        "password": "hunter22",
        "full_name": "Dana Driver",
    }
    first = client.post("/users/register", json=payload)
    assert first.status_code == 201

    second = client.post("/users/register", json=payload)
    assert second.status_code == 400


def test_login_success_returns_token(client):
    client.post(
        "/users/register",
        json={"email": "driver@example.com", "password": "hunter22", "full_name": "Dana Driver"},
    )

    response = client.post(
        "/users/login", json={"email": "driver@example.com", "password": "hunter22"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "driver@example.com"
    assert body["access_token"]


def test_login_wrong_password_is_rejected(client):
    client.post(
        "/users/register",
        json={"email": "driver@example.com", "password": "hunter22", "full_name": "Dana Driver"},
    )

    response = client.post(
        "/users/login", json={"email": "driver@example.com", "password": "wrong-password"}
    )
    assert response.status_code == 401


def test_profile_requires_auth(client):
    response = client.get("/users/profile")
    assert response.status_code == 403


def test_profile_returns_current_user(client, auth_headers):
    response = client.get("/users/profile", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "driver@example.com"
