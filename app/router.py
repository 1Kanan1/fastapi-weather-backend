from app.services import WeatherService, LocationService
from fastapi import APIRouter, Query, Depends
from app.schemas import (
    SearchResponse,
    WeatherResponse,
    CitySuggestion,
)

router = APIRouter()


async def get_location_service():
    return LocationService()


async def get_weather_service():
    return WeatherService()


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1),
    service: LocationService = Depends(get_location_service),
):
    """Search for cities or countries."""
    cities = await service.search(q)
    return {"cities": cities}


@router.get("/nearest", response_model=CitySuggestion)
async def nearest(
    lat: float = Query(...),
    lon: float = Query(...),
    service: LocationService = Depends(get_location_service),
):
    """Find the nearest city in the database to the given coordinates."""
    return await service.find_nearest(lat, lon)


@router.get("/weather", response_model=WeatherResponse)
async def weather(
    lat: float = Query(...),
    lon: float = Query(...),
    service: WeatherService = Depends(get_weather_service),
):
    """Retrieve weather data via Open-Meteo."""
    return await service.fetch_weather(lat, lon)
