"""Application configuration management"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    DATABASE_URL: str

    # JWT Authentication
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Cloudinary (optional)
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None

    # AI/LLM Configuration (optional)
    OPENAI_API_BASE: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    AI_MODEL: Optional[str] = None

    # Application
    APP_NAME: str = "CreativePulse AI"
    DEBUG: bool = False

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @property
    def cloudinary_configured(self) -> bool:
        """Check if Cloudinary is properly configured"""
        return all([
            self.CLOUDINARY_CLOUD_NAME,
            self.CLOUDINARY_API_KEY,
            self.CLOUDINARY_API_SECRET
        ])

    @property
    def ai_configured(self) -> bool:
        """Check if AI/LLM is properly configured"""
        return all([
            self.OPENAI_API_BASE,
            self.OPENAI_API_KEY
        ])

    def validate_required(self) -> None:
        """Validate that required configuration is present"""
        required = {
            "DATABASE_URL": self.DATABASE_URL,
            "JWT_SECRET": self.JWT_SECRET,
        }

        missing = [key for key, value in required.items() if not value]

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        if len(self.JWT_SECRET) < 32:
            raise ValueError(
                "JWT_SECRET must be at least 32 characters long for security"
            )


# Global settings instance
settings = Settings()

try:
    settings.validate_required()
except ValueError as e:
    import sys
    print(f"WARNING: Configuration Error: {e}", file=sys.stderr)
    print("Please check your .env file and ensure all required variables are set.")
    print("See .env.example for reference.")
