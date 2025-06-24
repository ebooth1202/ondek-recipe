# Update your config.py
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

if not os.getenv("DYNO"):
    load_dotenv()

class Settings(BaseSettings):
    # MongoDB connection
    mongo_uri: str = os.getenv("MONGO_URI") or os.getenv("MONGODB_URL")

    # Security
    secret_key: str = os.getenv("SECRET_KEY")

    # Environment
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "development")

    # AI Integration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Domain configuration
    domain: str = os.getenv("DOMAIN", "localhost")
    api_subdomain: str = os.getenv("API_SUBDOMAIN", "")

    # Base URL for the application
    @property
    def base_url(self) -> str:
        if self.is_production():
            # For Heroku, use the full domain without subdomain
            if self.api_subdomain and self.api_subdomain.strip():
                return f"https://{self.api_subdomain}.{self.domain}"
            else:
                return f"https://{self.domain}"
        return "http://127.0.0.1:8000"

    # Frontend URL
    @property
    def frontend_url(self) -> str:
        if self.is_production():
            return f"https://{self.domain}"
        return "http://localhost:3000"

    # Database name
    database_name: str = os.getenv("DATABASE_NAME", "ondek_recipe")

    class Config:
        env_file = ".env"
        case_sensitive = False

    def is_production(self) -> bool:
        return self.environment == "production" or bool(os.getenv("DYNO"))

settings = Settings()