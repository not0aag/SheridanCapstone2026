def _other_user_headers(client):
    client.post(
        "/users/register",
        json={"email": "other@example.com", "password": "hunter2", "full_name": "Other Driver"},
    )
    login = client.post(
        "/users/login", json={"email": "other@example.com", "password": "hunter2"}
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _start_trip(client, headers):
    return client.post("/trips/start", headers=headers, json={}).json()["id"]


def test_create_incident_on_own_trip(client, auth_headers):
    trip_id = _start_trip(client, auth_headers)

    response = client.post(
        "/incidents/",
        headers=auth_headers,
        json={"trip_id": trip_id, "incident_type": "distraction", "severity": "low"},
    )
    assert response.status_code == 201
    assert response.json()["trip_id"] == trip_id


def test_cannot_create_incident_on_another_users_trip(client, auth_headers):
    trip_id = _start_trip(client, auth_headers)

    other_headers = _other_user_headers(client)
    response = client.post(
        "/incidents/",
        headers=other_headers,
        json={"trip_id": trip_id, "incident_type": "distraction", "severity": "low"},
    )
    assert response.status_code == 404


def test_create_incident_requires_auth(client):
    response = client.post(
        "/incidents/", json={"trip_id": 1, "incident_type": "distraction", "severity": "low"}
    )
    assert response.status_code == 403


def test_cannot_list_incidents_for_another_users_trip(client, auth_headers):
    trip_id = _start_trip(client, auth_headers)
    client.post(
        "/incidents/",
        headers=auth_headers,
        json={"trip_id": trip_id, "incident_type": "drowsiness", "severity": "medium"},
    )

    other_headers = _other_user_headers(client)
    response = client.get(f"/incidents/trip/{trip_id}", headers=other_headers)
    assert response.status_code == 404


def test_cannot_get_another_users_incident(client, auth_headers):
    trip_id = _start_trip(client, auth_headers)
    incident = client.post(
        "/incidents/",
        headers=auth_headers,
        json={"trip_id": trip_id, "incident_type": "crash", "severity": "high"},
    ).json()

    other_headers = _other_user_headers(client)
    response = client.get(f"/incidents/{incident['id']}", headers=other_headers)
    assert response.status_code == 404


def test_get_own_incident(client, auth_headers):
    trip_id = _start_trip(client, auth_headers)
    incident = client.post(
        "/incidents/",
        headers=auth_headers,
        json={"trip_id": trip_id, "incident_type": "crash", "severity": "high"},
    ).json()

    response = client.get(f"/incidents/{incident['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == incident["id"]


def test_cannot_list_another_users_incidents(client, auth_headers):
    me = client.get("/users/profile", headers=auth_headers).json()

    other_headers = _other_user_headers(client)
    response = client.get(f"/incidents/user/{me['id']}", headers=other_headers)
    assert response.status_code == 403
