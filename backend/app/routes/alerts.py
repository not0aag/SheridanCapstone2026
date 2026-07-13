from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.distraction_alert import DistractionAlert
from app.models.emergency_contact import EmergencyContact
from app.models.user import User
from app.auth import get_current_user
from app.services import notifications

router = APIRouter(prefix="/alerts", tags=["alerts"])

# A driver stays continuously distracted for a while before the app fires a
# second alert; this is a server-side floor independent of that client-side
# cooldown, since the client's cooldown only lives in memory and resets if
# the app is killed and relaunched mid-drive.
MIN_ALERT_INTERVAL = timedelta(minutes=2)

# Pydantic schemas
class DistractionAlertCreate(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    trip_id: Optional[int] = None

class DistractionAlertResponse(BaseModel):
    id: int
    contacts_notified: int
    sent_at: datetime

    class Config:
        from_attributes = True

@router.post("/distraction", response_model=DistractionAlertResponse, status_code=201)
def trigger_distraction_alert(
    alert_data: DistractionAlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    last_alert = (
        db.query(DistractionAlert)
        .filter(DistractionAlert.user_id == current_user.id)
        .order_by(DistractionAlert.sent_at.desc())
        .first()
    )
    if last_alert:
        last_sent_at = last_alert.sent_at
        if last_sent_at.tzinfo is None:
            last_sent_at = last_sent_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - last_sent_at < MIN_ALERT_INTERVAL:
            raise HTTPException(status_code=429, detail="Distraction alert already sent recently")

    contacts = (
        db.query(EmergencyContact)
        .filter(EmergencyContact.user_id == current_user.id)
        .all()
    )

    contacts_notified = notifications.send_distraction_alerts(driver=current_user, contacts=contacts)

    record = DistractionAlert(
        user_id=current_user.id,
        trip_id=alert_data.trip_id,
        latitude=alert_data.latitude,
        longitude=alert_data.longitude,
        contacts_notified=contacts_notified,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return record
