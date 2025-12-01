from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    s3_bucket = Column(String(255), nullable=False)
    s3_key = Column(String(500), nullable=False)
    file_size_mb = Column(Numeric(10, 2), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    resolution = Column(String(20), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
