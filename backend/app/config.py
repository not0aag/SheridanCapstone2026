from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql://postgres:Neil123!!@localhost:5432/safedrive_dev"
    
    # API settings
    API_TITLE: str = "SafeDrive AI Backend"
    API_VERSION: str = "1.0.0"
    
    # S3 settings
    USE_S3: bool = False  # Set to True when AWS is ready
    S3_BUCKET_NAME: str = "safedrive-videos-dev"
    AWS_ACCESS_KEY_ID: str = ""  # Add when AWS is ready
    AWS_SECRET_ACCESS_KEY: str = ""  # Add when AWS is ready
    AWS_REGION: str = "us-east-1"
    
    class Config:
        env_file = ".env"

settings = Settings()
