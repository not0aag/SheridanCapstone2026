from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.database import get_db
from app.models.incident import Incident
from app.models.trip import Trip

router = APIRouter(prefix="/incidents", tags=["incidents"])

# Pydantic schemas
class IncidentCreate(BaseModel):
    trip_id: int
    incident_type: str  # distraction, crash, drowsiness
    severity: str  # low, medium, high
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None

class IncidentResponse(BaseModel):
    id: int
    trip_id: int
    incident_type: str
    severity: str
    timestamp: datetime
    latitude: Optional[float]
    longitude: Optional[float]
    description: Optional[str]
    
    class Config:
        from_attributes = True

# Create incident endpoint
@router.post("/", response_model=IncidentResponse, status_code=201)
def create_incident(incident_data: IncidentCreate, db: Session = Depends(get_db)):
    # Verify trip exists
    trip = db.query(Trip).filter(Trip.id == incident_data.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Validate incident type
    valid_types = ["distraction", "crash", "drowsiness"]
    if incident_data.incident_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid incident type. Must be one of: {valid_types}")
    
    # Validate severity
    valid_severities = ["low", "medium", "high"]
    if incident_data.severity not in valid_severities:
        raise HTTPException(status_code=400, detail=f"Invalid severity. Must be one of: {valid_severities}")
    
    # Create incident
    new_incident = Incident(
        trip_id=incident_data.trip_id,
        incident_type=incident_data.incident_type,
        severity=incident_data.severity,
        timestamp=datetime.utcnow(),
        latitude=incident_data.latitude,
        longitude=incident_data.longitude,
        description=incident_data.description
    )
    
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)
    
    return new_incident

# Get all incidents for a trip
@router.get("/trip/{trip_id}", response_model=list[IncidentResponse])
def get_trip_incidents(trip_id: int, db: Session = Depends(get_db)):
    # Verify trip exists
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    incidents = db.query(Incident).filter(Incident.trip_id == trip_id).order_by(Incident.timestamp.desc()).all()
    return incidents

# Get specific incident
@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return incident

# Get all incidents for a user (across all trips)
@router.get("/user/{user_id}", response_model=list[IncidentResponse])
def get_user_incidents(user_id: int, db: Session = Depends(get_db)):
    incidents = (
        db.query(Incident)
        .join(Trip)
        .filter(Trip.user_id == user_id)
        .order_by(Incident.timestamp.desc())
        .all()
    )
    return incidents
