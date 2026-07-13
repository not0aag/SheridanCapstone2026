from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql://postgres:Neil123!!@localhost:5432/safedrive_dev"
    
    # API settings
    API_TITLE: str = "SafeDrive AI Backend"
    API_VERSION: str = "1.0.0"
    
    # S3 settings
    USE_S3: bool = True  # Changed to True - using real S3 now!
    S3_BUCKET_NAME: str = "safedrive-videos-dev-neil"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"

    # Twilio settings (SMS alerts to trusted contacts). Empty values fall
    # back to a dry-run mode in app.services.notifications.
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
