import httpx
from fastapi import HTTPException
from cashews import cache
from app.config import settings
from anyio import to_thread
from app.database import db_session, LocationRepository
from app.schemas import (
    CitySuggestion,
    WeatherResponse,
    CurrentWeather,
    HourlyWeather,
    DailyWeather,
)
from typing import List

cache.setup("mem://")


class LocationService:
    """
    Business Logic for Locations.
    Orchestrates the 'Country-first' search strategy.
    """

    async def search(self, query: str) -> List[CitySuggestion]:
        clean_query = query.strip()
        if not clean_query:
            return []

        # Use to_thread as SQLite is synchronous/blocking
        return await to_thread.run_sync(self._execute_search, clean_query)

    def _execute_search(self, query: str) -> List[CitySuggestion]:
        """Synchronous search orchestration inside the thread pool."""
        with db_session() as conn:
            repo = LocationRepository(conn)
            country_id = repo.find_country_id(query)

            if country_id:
                return repo.get_cities_by_country(country_id)

            return repo.get_cities_by_name(query)

    async def find_nearest(self, lat: float, lon: float) -> CitySuggestion:
        """Find the nearest city to coordinates asynchronously using thread pool."""
        return await to_thread.run_sync(self._execute_find_nearest, lat, lon)

    def _execute_find_nearest(self, lat: float, lon: float) -> CitySuggestion:
        """Synchronous database call within the thread pool."""
        with db_session() as conn:
            repo = LocationRepository(conn)
            return repo.find_nearest_city(lat, lon)


class WeatherService:
    """
    External API orchestration.
    Handles URL construction and communication with Open-Meteo.
    """

    def __init__(self):
        self.url = settings.OPEN_METEO_URL

    def _get_fields(self, model) -> str:
        """Helper to extract Pydantic fields for the API request."""
        return ",".join([f for f in model.model_fields.keys() if f != "time"])

    @cache(ttl="15m", key="weather:{lat}:{lon}")
    async def fetch_weather(self, lat: float, lon: float) -> WeatherResponse:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": self._get_fields(CurrentWeather),
            "hourly": self._get_fields(HourlyWeather),
            "daily": self._get_fields(DailyWeather),
            "timezone": "auto",
            "forecast_hours": 24,
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.url, params=params)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Open-Meteo error: {e.response.text}"
                )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to reach Open-Meteo: {str(e)}"
                )
            try:
                return WeatherResponse(**response.json())
            except Exception as e:
                raise HTTPException(
                    status_code=502,
                    detail=f"Invalid payload structure from Open-Meteo: {str(e)}"
                )
