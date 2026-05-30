from pydantic import BaseModel, Field
from typing import Optional, List


class CitySuggestion(BaseModel):
    id: int = Field(..., description="Unique identifier for the city")
    name: str = Field(..., description="Full name of the city")
    state_code: str = Field(..., description="Short code for the state/province")
    country_code: str = Field(..., description="2-letter ISO country code")
    latitude: float = Field(..., description="Decimal latitude for weather lookups")
    longitude: float = Field(..., description="Decimal longitude for weather lookups")
    population: Optional[int] = Field(
        None, description="City population used for ranking suggestions"
    )


class SearchResponse(BaseModel):
    cities: List[CitySuggestion] = Field(
        ..., description="List of city suggestions matching the search query"
    )


# --- Weather Schemas ---


class CurrentWeather(BaseModel):
    time: str = Field(..., description="Current timestamp")
    temperature_2m: float = Field(..., description="Current temperature in Celsius")
    weather_code: int = Field(..., description="WMO weather interpretation code")
    apparent_temperature: float = Field(..., description="Feels-like temperature")
    relative_humidity_2m: int = Field(..., description="Relative humidity percentage")
    wind_speed_10m: float = Field(..., description="Wind speed in km/h")
    is_day: int | float = Field(..., description="1 for day, 0 for night")


class HourlyWeather(BaseModel):
    time: List[str] = Field(..., description="Hourly timestamps")
    temperature_2m: List[float] = Field(..., description="Hourly temperatures")
    precipitation_probability: List[int] = Field(
        ..., description="Hourly precipitation probability"
    )
    weather_code: List[int] = Field(..., description="Hourly weather codes")


class DailyWeather(BaseModel):
    time: List[str] = Field(..., description="Daily dates")
    weather_code: List[int] = Field(..., description="Daily weather codes")
    temperature_2m_max: List[float] = Field(..., description="Daily max temperatures")
    temperature_2m_min: List[float] = Field(..., description="Daily min temperatures")
    precipitation_probability_max: List[int] = Field(
        ..., description="Max precipitation probability for the day"
    )
    uv_index_max: List[float] = Field(..., description="Daily max UV index")
    sunset: List[str] = Field(..., description="Sunset times")
    sunrise: List[str] = Field(..., description="Sunrise times")


class WeatherResponse(BaseModel):
    latitude: float = Field(..., description="Latitude of the location")
    longitude: float = Field(..., description="Longitude of the location")
    timezone: str | None = Field(..., description="Timezone name")
    current: CurrentWeather
    hourly: HourlyWeather
    daily: DailyWeather
