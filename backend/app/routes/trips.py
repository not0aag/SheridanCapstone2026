from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.database import get_db
from app.models.trip import Trip
from app.models.user import User
from app.auth import get_current_user

router = APIRouter(prefix="/trips", tags=["trips"])

# Pydantic schemas
class TripStart(BaseModel):
    start_location: Optional[str] = None

class TripStop(BaseModel):
    end_location: Optional[str] = None
    distance_km: Optional[float] = None
    safety_score: Optional[int] = None

class TripResponse(BaseModel):
    id: int
    user_id: int
    start_time: datetime
    end_time: Optional[datetime]
    distance_km: Optional[float]
    start_location: Optional[str]
    end_location: Optional[str]
    safety_score: Optional[int]
    status: str
    
    class Config:
        from_attributes = True

# Start trip endpoint
@router.post("/start", response_model=TripResponse, status_code=201)
def start_trip(
    trip_data: TripStart,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Create new trip
    new_trip = Trip(
        user_id=current_user.id,
        start_time=datetime.utcnow(),
        start_location=trip_data.start_location,
        status="active"
    )

    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)

    return new_trip

# Stop trip endpoint
@router.post("/stop/{trip_id}", response_model=TripResponse)
def stop_trip(
    trip_id: int,
    trip_data: TripStop,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Find trip
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.status != "active":
        raise HTTPException(status_code=400, detail="Trip is not active")

    # Update trip
    trip.end_time = datetime.utcnow()
    trip.end_location = trip_data.end_location
    trip.distance_km = trip_data.distance_km
    trip.safety_score = trip_data.safety_score
    trip.status = "completed"

    db.commit()
    db.refresh(trip)

    return trip

# Get all trips for a user
@router.get("/user/{user_id}", response_model=list[TripResponse])
def get_user_trips(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view these trips")
    trips = db.query(Trip).filter(Trip.user_id == user_id).order_by(Trip.start_time.desc()).all()
    return trips

# Get specific trip
@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    return trip
