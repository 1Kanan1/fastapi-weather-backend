import sqlite3
from typing import List, Optional
from contextlib import contextmanager
from app.config import settings
from app.schemas import CitySuggestion


@contextmanager
def db_session():
    """Manages SQLite connection lifecycle."""
    conn = sqlite3.connect(settings.DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class LocationRepository:
    """Encapsulates all database queries for locations."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def find_country_id(self, name: str) -> Optional[int]:
        """Returns country ID if the name matches a country."""
        row = self.conn.execute(
            "SELECT id FROM countries WHERE name LIKE ? LIMIT 1", (f"{name}%",)
        ).fetchone()
        return row["id"] if row else None

    def get_cities_by_country(
        self, country_id: int, limit: int = 20
    ) -> List[CitySuggestion]:
        """Fetches most populated cities for a given country ID."""
        rows = self.conn.execute(
            """
            SELECT id, name, state_code, country_code, latitude, longitude, population
            FROM cities
            WHERE country_code = (SELECT iso2 FROM countries WHERE id = ?)
            ORDER BY population DESC LIMIT ?
        """,
            (country_id, limit),
        ).fetchall()
        return [CitySuggestion(**dict(r)) for r in rows]

    def get_cities_by_name(self, name: str, limit: int = 20) -> List[CitySuggestion]:
        """Fetches cities matching a name query, ranked by population."""
        rows = self.conn.execute(
            """
            SELECT id, name, state_code, country_code, latitude, longitude, population
            FROM cities
            WHERE name LIKE ?
            ORDER BY population DESC LIMIT ?
        """,
            (f"{name}%", limit),
        ).fetchall()
        return [CitySuggestion(**dict(r)) for r in rows]

    def find_nearest_city(self, lat: float, lon: float) -> CitySuggestion:
        """Fetches the single closest city to the given coordinates."""
        row = self.conn.execute(
            """
            SELECT id, name, state_code, country_code, latitude, longitude, population
            FROM cities
            ORDER BY ((latitude - ?) * (latitude - ?) + (longitude - ?) * (longitude - ?)) ASC
            LIMIT 1
        """,
            (lat, lat, lon, lon),
        ).fetchone()
        if not row:
            raise ValueError("no cities found in database.")
        return CitySuggestion(**dict(row))
