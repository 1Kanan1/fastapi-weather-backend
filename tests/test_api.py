import sys
import os
# Dynamic path resolution to include server/ in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from main import app
from app.services import WeatherService

client = TestClient(app)


def test_search_valid():
    """Verify that a valid city search returns results successfully."""
    response = client.get("/search?q=Baku")
    assert response.status_code == 200
    data = response.json()
    assert "cities" in data
    assert len(data["cities"]) > 0
    
    city = data["cities"][0]
    assert "id" in city
    assert "name" in city
    assert "latitude" in city
    assert "longitude" in city
    assert "country_code" in city


def test_search_validation_error():
    """Verify that an empty query string returns a 422 validation error."""
    response = client.get("/search?q=")
    assert response.status_code == 422


def test_weather_valid():
    """Verify that coordinates query returns correct weather payload structure."""
    response = client.get("/weather?lat=40.4093&lon=49.8671")
    assert response.status_code == 200
    data = response.json()
    
    assert "latitude" in data
    assert "longitude" in data
    assert "current" in data
    assert "hourly" in data
    assert "daily" in data
    
    assert "temperature_2m" in data["current"]
    assert "weather_code" in data["current"]
    assert "apparent_temperature" in data["current"]
    
    assert len(data["hourly"]["time"]) > 0
    assert len(data["daily"]["time"]) > 0


def test_weather_validation_error():
    """Verify that missing query coordinates returns a 422 error."""
    response = client.get("/weather?lat=40.4093")
    assert response.status_code == 422


def test_nearest_valid():
    """Verify that coordinates query returns the nearest city suggest payload."""
    response = client.get("/nearest?lat=40.4093&lon=49.8671")
    assert response.status_code == 200
    data = response.json()
    
    assert "id" in data
    assert "name" in data
    assert "latitude" in data
    assert "longitude" in data
    assert "country_code" in data
    assert data["name"] == "Baku"  # Baku coordinates


def test_nearest_validation_error():
    """Verify that missing coordinates returns a 422 error for nearest city."""
    response = client.get("/nearest?lat=40.4093")
    assert response.status_code == 422


@pytest.mark.anyio
async def test_weather_cache_works():
    """Verify that calling the weather service twice returns cached results without duplicate network requests."""
    service = WeatherService()
    lat, lon = 40.4093, 49.8671
    
    mock_response_data = {
        "latitude": 40.4,
        "longitude": 49.8,
        "timezone": "Asia/Baku",
        "current": {
            "time": "2026-05-28T20:00:00Z",
            "temperature_2m": 22.4,
            "weather_code": 0,
            "apparent_temperature": 21.8,
            "relative_humidity_2m": 62,
            "wind_speed_10m": 12.5,
            "is_day": 1
        },
        "hourly": {
            "time": ["2026-05-28T00:00"],
            "temperature_2m": [20.1],
            "precipitation_probability": [0],
            "weather_code": [0]
        },
        "daily": {
            "time": ["2026-05-28"],
            "weather_code": [0],
            "temperature_2m_max": [25.4],
            "temperature_2m_min": [16.2],
            "precipitation_probability_max": [20],
            "uv_index_max": [5.2],
            "sunrise": ["2026-05-28T05:24"],
            "sunset": ["2026-05-28T20:12"]
        }
    }
    
    # Clear the cashews cache first to ensure a clean state
    from cashews import cache
    await cache.clear()
    
    # Mock the httpx AsyncClient.get method
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        # Mock response object returning the mock JSON
        mock_response = AsyncMock()
        mock_response.json = lambda: mock_response_data
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response
        
        # First call: should trigger a network fetch
        res1 = await service.fetch_weather(lat, lon)
        assert res1.current.temperature_2m == 22.4
        assert mock_get.call_count == 1
        
        # Second call: should read directly from cache (mock_get call_count remains 1)
        res2 = await service.fetch_weather(lat, lon)
        assert res2.current.temperature_2m == 22.4
        assert mock_get.call_count == 1
