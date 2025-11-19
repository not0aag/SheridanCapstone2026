from fastapi import FastAPI
from app.config import settings
from app.routes.users import router as users_router

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION
)

# Include routers
app.include_router(users_router)

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "SafeDrive AI Backend API",
        "version": settings.API_VERSION,
        "status": "running"
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "safedrive-backend"
    }
