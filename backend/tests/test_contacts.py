def test_create_and_list_contact(client, auth_headers):
    create = client.post(
        "/contacts/",
        headers=auth_headers,
        json={"name": "Sam Contact", "phone_number": "+15551234567", "relationship": "spouse"},
    )
    assert create.status_code == 201
    body = create.json()
    assert body["name"] == "Sam Contact"
    assert body["phone_number"] == "+15551234567"
    assert body["relationship"] == "spouse"

    listing = client.get("/contacts/", headers=auth_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["name"] == "Sam Contact"


def test_contacts_require_auth(client):
    response = client.get("/contacts/")
    assert response.status_code == 403


def test_delete_contact(client, auth_headers):
    create = client.post(
        "/contacts/",
        headers=auth_headers,
        json={"name": "Sam Contact", "phone_number": "+15551234567"},
    )
    contact_id = create.json()["id"]

    delete = client.delete(f"/contacts/{contact_id}", headers=auth_headers)
    assert delete.status_code == 204

    listing = client.get("/contacts/", headers=auth_headers)
    assert listing.json() == []


def test_delete_missing_contact_is_404(client, auth_headers):
    response = client.delete("/contacts/999", headers=auth_headers)
    assert response.status_code == 404


def test_cannot_delete_another_users_contact(client, auth_headers):
    create = client.post(
        "/contacts/",
        headers=auth_headers,
        json={"name": "Sam Contact", "phone_number": "+15551234567"},
    )
    contact_id = create.json()["id"]

    client.post(
        "/users/register",
        json={
            "email": "other@example.com",
            "password": "hunter2",
            "full_name": "Other Driver",
        },
    )
    other_login = client.post(
        "/users/login", json={"email": "other@example.com", "password": "hunter2"}
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    response = client.delete(f"/contacts/{contact_id}", headers=other_headers)
    assert response.status_code == 404
