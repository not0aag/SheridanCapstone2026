import logging

from twilio.rest import Client

from app.config import settings

logger = logging.getLogger(__name__)


def _client() -> Client | None:
    """Returns a Twilio client, or None if no credentials are configured.

    Absence of credentials is treated as dry-run mode rather than an error,
    so the alert flow works end-to-end in local/dev/CI environments that
    don't have a Twilio account.
    """
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        return None
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def send_distraction_alerts(driver, contacts) -> int:
    """Sends a distraction SMS alert to each contact. Returns the number sent.

    A per-contact send failure is logged and skipped rather than aborting
    the whole batch, so one bad number doesn't stop the rest of the driver's
    contacts from being notified.
    """
    driver_name = driver.full_name or "A driver you know"
    body = (
        f"SafeDrive AI Alert: {driver_name} may be distracted while driving. "
        f"This is an automated safety notification."
    )

    client = _client()
    sent = 0
    for contact in contacts:
        if client is None:
            logger.info("[DRY RUN] Would SMS %s: %s", contact.phone_number, body)
            sent += 1
            continue
        try:
            client.messages.create(
                body=body,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=contact.phone_number,
            )
            sent += 1
        except Exception:
            logger.exception("Twilio send failed for contact %s", contact.id)

    return sent
