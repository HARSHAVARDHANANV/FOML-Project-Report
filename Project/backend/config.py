"""
Configuration management for Customer Segmentation API.
Loads settings from environment variables using python-dotenv.
"""
import os
from functools import lru_cache
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # CORS Configuration
    CORS_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8001,http://127.0.0.1:5500,http://127.0.0.1:8001").split(",")
    ]

    # Server Configuration
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    SERVER_ENVIRONMENT: str = os.getenv("SERVER_ENVIRONMENT", "development")

    # Data Configuration
    DATASET_PATH: str = os.getenv("DATASET_PATH", "../Customers_dataset.csv")

    # API Configuration
    API_TITLE: str = "Customer Segmentation API"
    API_VERSION: str = "1.0.0"

    # Validation constraints
    INCOME_MAX: float = float(os.getenv("INCOME_MAX", "1000000"))
    INCOME_MIN: float = float(os.getenv("INCOME_MIN", "0"))
    SPENDING_SCORE_MAX: float = float(os.getenv("SPENDING_SCORE_MAX", "100"))
    SPENDING_SCORE_MIN: float = float(os.getenv("SPENDING_SCORE_MIN", "1"))
    FREQUENCY_MAX: float = float(os.getenv("FREQUENCY_MAX", "365"))
    FREQUENCY_MIN: float = float(os.getenv("FREQUENCY_MIN", "0"))
    RECENCY_MAX: float = float(os.getenv("RECENCY_MAX", "3650"))
    RECENCY_MIN: float = float(os.getenv("RECENCY_MIN", "0"))
    MONETARY_MAX: float = float(os.getenv("MONETARY_MAX", "1000000"))
    MONETARY_MIN: float = float(os.getenv("MONETARY_MIN", "0"))


@lru_cache()
def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
