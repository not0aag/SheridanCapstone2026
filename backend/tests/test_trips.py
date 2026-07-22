def _other_user_headers(client):
    client.post(
        "/users/register",
        json={"email": "other@example.com", "password": "hunter2", "full_name": "Other Driver"},
    )
    login = client.post(
        "/users/login", json={"email": "other@example.com", "password": "hunter2"}
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_start_trip_uses_authenticated_user(client, auth_headers):
    response = client.post(
        "/trips/start", headers=auth_headers, json={"start_location": "Home"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["start_location"] == "Home"
    assert body["status"] == "active"


def test_start_trip_requires_auth(client):
    response = client.post("/trips/start", json={"start_location": "Home"})
    assert response.status_code == 403


def test_stop_trip(client, auth_headers):
    start = client.post("/trips/start", headers=auth_headers, json={})
    trip_id = start.json()["id"]

    response = client.post(
        f"/trips/stop/{trip_id}",
        headers=auth_headers,
        json={"end_location": "Work", "distance_km": 12.5, "safety_score": 90},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["end_location"] == "Work"


def test_cannot_stop_another_users_trip(client, auth_headers):
    start = client.post("/trips/start", headers=auth_headers, json={})
    trip_id = start.json()["id"]

    other_headers = _other_user_headers(client)
    response = client.post(
        f"/trips/stop/{trip_id}", headers=other_headers, json={}
    )
    assert response.status_code == 404


def test_cannot_get_another_users_trip(client, auth_headers):
    start = client.post("/trips/start", headers=auth_headers, json={})
    trip_id = start.json()["id"]

    other_headers = _other_user_headers(client)
    response = client.get(f"/trips/{trip_id}", headers=other_headers)
    assert response.status_code == 404


def test_get_own_trip(client, auth_headers):
    start = client.post("/trips/start", headers=auth_headers, json={})
    trip_id = start.json()["id"]

    response = client.get(f"/trips/{trip_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == trip_id


def test_cannot_list_another_users_trips(client, auth_headers):
    me = client.get("/users/profile", headers=auth_headers).json()
    client.post("/trips/start", headers=auth_headers, json={})

    other_headers = _other_user_headers(client)
    response = client.get(f"/trips/user/{me['id']}", headers=other_headers)
    assert response.status_code == 403


def test_list_own_trips(client, auth_headers):
    me = client.get("/users/profile", headers=auth_headers).json()
    client.post("/trips/start", headers=auth_headers, json={})

    response = client.get(f"/trips/user/{me['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
