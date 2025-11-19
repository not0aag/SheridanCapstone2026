from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql://postgres:Neil123!!@localhost:5432/safedrive_dev"
    
    # API settings
    API_TITLE: str = "SafeDrive AI Backend"
    API_VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"

settings = Settings()
