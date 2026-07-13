from unittest.mock import MagicMock, patch


def test_distraction_alert_with_no_contacts_still_succeeds(client, auth_headers):
    response = client.post("/alerts/distraction", headers=auth_headers, json={})
    assert response.status_code == 201
    assert response.json()["contacts_notified"] == 0


def test_distraction_alert_dry_run_notifies_contacts(client, auth_headers):
    # No TWILIO_* settings are configured in tests, so this exercises the
    # dry-run branch of app.services.notifications.send_distraction_alerts.
    client.post(
        "/contacts/",
        headers=auth_headers,
        json={"name": "Sam Contact", "phone_number": "+15551234567"},
    )
    client.post(
        "/contacts/",
        headers=auth_headers,
        json={"name": "Alex Contact", "phone_number": "+15557654321"},
    )

    response = client.post(
        "/alerts/distraction",
        headers=auth_headers,
        json={"latitude": 43.65, "longitude": -79.38},
    )
    assert response.status_code == 201
    assert response.json()["contacts_notified"] == 2


def test_repeated_distraction_alert_is_rate_limited(client, auth_headers):
    client.post(
        "/contacts/",
        headers=auth_headers,
        json={"name": "Sam Contact", "phone_number": "+15551234567"},
    )

    first = client.post("/alerts/distraction", headers=auth_headers, json={})
    assert first.status_code == 201

    second = client.post("/alerts/distraction", headers=auth_headers, json={})
    assert second.status_code == 429


def test_alerts_require_auth(client):
    response = client.post("/alerts/distraction", json={})
    assert response.status_code == 403


def test_distraction_alert_sends_real_sms_when_twilio_configured(client, auth_headers):
    client.post(
        "/contacts/",
        headers=auth_headers,
        json={"name": "Sam Contact", "phone_number": "+15551234567"},
    )

    mock_client = MagicMock()
    with patch("app.services.notifications._client", return_value=mock_client):
        response = client.post("/alerts/distraction", headers=auth_headers, json={})

    assert response.status_code == 201
    assert response.json()["contacts_notified"] == 1
    mock_client.messages.create.assert_called_once()
    _, kwargs = mock_client.messages.create.call_args
    assert kwargs["to"] == "+15551234567"
