import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    mongo_uri: str = os.getenv("MONGO_URI")
    secret_key: str = os.getenv("SECRET_KEY")
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    class Config:
        env_file = ".env"


settings = Settings()