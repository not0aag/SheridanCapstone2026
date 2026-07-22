from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import os
import uuid
import tempfile
from app.database import get_db
from app.models.video import Video
from app.models.incident import Incident
from app.models.trip import Trip
from app.models.user import User
from app.auth import get_current_user
from app.s3_config import s3_handler

router = APIRouter(prefix="/videos", tags=["videos"])

# Reject uploads larger than this before writing anything to disk/S3.
MAX_VIDEO_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB


def _owned_incident_or_404(db: Session, incident_id: int, current_user: User) -> Incident:
    incident = (
        db.query(Incident)
        .join(Trip)
        .filter(Incident.id == incident_id, Trip.user_id == current_user.id)
        .first()
    )
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident

# Pydantic schemas
class VideoUpload(BaseModel):
    incident_id: int
    duration_seconds: Optional[int] = None
    resolution: Optional[str] = None

class VideoResponse(BaseModel):
    id: int
    incident_id: int
    s3_bucket: str
    s3_key: str
    file_size_mb: Optional[float]
    duration_seconds: Optional[int]
    resolution: Optional[str]
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

# Upload video endpoint
@router.post("/upload", response_model=VideoResponse, status_code=201)
async def upload_video(
    file: UploadFile = File(...),
    incident_id: int = None,
    duration_seconds: Optional[int] = None,
    resolution: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload video file to S3 and save metadata to database"""

    # Validate incident exists and belongs to the caller
    if incident_id:
        _owned_incident_or_404(db, incident_id, current_user)

    # Validate file type
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")

    temp_path = None
    try:
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        object_key = f"videos/incidents/{datetime.now().year}/{datetime.now().month:02d}/{unique_filename}"

        # Save uploaded file temporarily (cross-platform), enforcing a size cap
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, unique_filename)
        size_bytes = 0
        with open(temp_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                size_bytes += len(chunk)
                if size_bytes > MAX_VIDEO_SIZE_BYTES:
                    raise HTTPException(status_code=413, detail="Video exceeds maximum upload size")
                buffer.write(chunk)

        file_size_mb = round(size_bytes / (1024 * 1024), 2)

        # Upload to S3
        upload_result = s3_handler.upload_video(temp_path, object_key)

        if not upload_result["success"]:
            raise HTTPException(status_code=500, detail=f"Upload failed: {upload_result.get('error')}")

        # Create video record
        new_video = Video(
            incident_id=incident_id,
            s3_bucket=upload_result["bucket"],
            s3_key=upload_result["key"],
            file_size_mb=file_size_mb,
            duration_seconds=duration_seconds,
            resolution=resolution
        )

        db.add(new_video)
        db.commit()
        db.refresh(new_video)

        return new_video

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

# Get video by ID
@router.get("/{video_id}", response_model=VideoResponse)
def get_video(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    video = (
        db.query(Video)
        .join(Incident, Video.incident_id == Incident.id)
        .join(Trip, Incident.trip_id == Trip.id)
        .filter(Video.id == video_id, Trip.user_id == current_user.id)
        .first()
    )

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return video

# Get video URL (pre-signed)
@router.get("/{video_id}/url")
def get_video_url(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    video = (
        db.query(Video)
        .join(Incident, Video.incident_id == Incident.id)
        .join(Trip, Incident.trip_id == Trip.id)
        .filter(Video.id == video_id, Trip.user_id == current_user.id)
        .first()
    )

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    try:
        url = s3_handler.get_video_url(video.s3_key)
        return {
            "video_id": video_id,
            "url": url,
            "expires_in": 3600  # 1 hour
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get all videos for an incident
@router.get("/incident/{incident_id}", response_model=list[VideoResponse])
def get_incident_videos(
    incident_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_incident_or_404(db, incident_id, current_user)
    videos = db.query(Video).filter(Video.incident_id == incident_id).all()
    return videos
