import app.routes.videos as videos_module


def _other_user_headers(client):
    client.post(
        "/users/register",
        json={"email": "other@example.com", "password": "hunter2", "full_name": "Other Driver"},
    )
    login = client.post(
        "/users/login", json={"email": "other@example.com", "password": "hunter2"}
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _own_incident(client, headers):
    trip_id = client.post("/trips/start", headers=headers, json={}).json()["id"]
    return client.post(
        "/incidents/",
        headers=headers,
        json={"trip_id": trip_id, "incident_type": "distraction", "severity": "low"},
    ).json()


def test_upload_video_on_own_incident(client, auth_headers):
    incident = _own_incident(client, auth_headers)

    response = client.post(
        "/videos/upload",
        headers=auth_headers,
        params={"incident_id": incident["id"]},
        files={"file": ("clip.mp4", b"fake video bytes", "video/mp4")},
    )
    assert response.status_code == 201
    assert response.json()["incident_id"] == incident["id"]


def test_cannot_upload_video_on_another_users_incident(client, auth_headers):
    incident = _own_incident(client, auth_headers)
    other_headers = _other_user_headers(client)

    response = client.post(
        "/videos/upload",
        headers=other_headers,
        params={"incident_id": incident["id"]},
        files={"file": ("clip.mp4", b"fake video bytes", "video/mp4")},
    )
    assert response.status_code == 404


def test_upload_requires_auth(client):
    response = client.post(
        "/videos/upload", files={"file": ("clip.mp4", b"data", "video/mp4")}
    )
    assert response.status_code == 403


def test_upload_rejects_non_video_content_type(client, auth_headers):
    response = client.post(
        "/videos/upload",
        headers=auth_headers,
        files={"file": ("notes.txt", b"not a video", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_rejects_oversized_video(client, auth_headers, monkeypatch):
    monkeypatch.setattr(videos_module, "MAX_VIDEO_SIZE_BYTES", 10)

    response = client.post(
        "/videos/upload",
        headers=auth_headers,
        files={"file": ("clip.mp4", b"this payload is bigger than ten bytes", "video/mp4")},
    )
    assert response.status_code == 413


def test_cannot_get_another_users_video(client, auth_headers):
    incident = _own_incident(client, auth_headers)
    video = client.post(
        "/videos/upload",
        headers=auth_headers,
        params={"incident_id": incident["id"]},
        files={"file": ("clip.mp4", b"fake video bytes", "video/mp4")},
    ).json()

    other_headers = _other_user_headers(client)
    response = client.get(f"/videos/{video['id']}", headers=other_headers)
    assert response.status_code == 404


def test_get_own_video(client, auth_headers):
    incident = _own_incident(client, auth_headers)
    video = client.post(
        "/videos/upload",
        headers=auth_headers,
        params={"incident_id": incident["id"]},
        files={"file": ("clip.mp4", b"fake video bytes", "video/mp4")},
    ).json()

    response = client.get(f"/videos/{video['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == video["id"]


def test_cannot_list_videos_for_another_users_incident(client, auth_headers):
    incident = _own_incident(client, auth_headers)
    other_headers = _other_user_headers(client)

    response = client.get(f"/videos/incident/{incident['id']}", headers=other_headers)
    assert response.status_code == 404
