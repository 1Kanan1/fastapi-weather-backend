import os
from pydantic_settings import BaseSettings

# Resolve the absolute path to the server/ directory
SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Settings(BaseSettings):
    DATABASE_NAME: str = os.path.join(SERVER_DIR, "weather-data.sqlite3")
    OPEN_METEO_URL: str = "https://api.open-meteo.com/v1/forecast"
    DEFAULT_SEARCH_LIMIT: int = 20


settings = Settings()
