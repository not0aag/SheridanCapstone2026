from fastapi import FastAPI
from app.config import settings
from app.routes.users import router as users_router
from app.routes.trips import router as trips_router
from app.routes.incidents import router as incidents_router

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION
)

# Include routers
app.include_router(users_router)
app.include_router(trips_router)
app.include_router(incidents_router)

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
