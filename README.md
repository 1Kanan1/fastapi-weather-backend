# weather (server)

A high-performance, lightweight weather API service built with **FastAPI**, **Uvicorn**, and **Python 3.13**. It acts as a smart weather proxy and geocoding engine—serving offline-capable location queries from a local SQLite database and proxying meteorological telemetry from the Open-Meteo API using an in-memory cache layer.

---

## 🗺️ system data flow

```
[ React 19 Client ]
       |
       |-- GET /search?q={query} ----------------------------+
       |-- GET /nearest?lat={lat}&lon={lon} -----------------+
       |-- GET /weather?lat={lat}&lon={lon} -------------+   |
                                                         |   |
                                                         v   v
                                                 [ FastAPI Server ]
                                                         |
                      +-- Local SQLite Query <-----------+
                      |   (weather-data.sqlite3)
                      |
                      +-- Proxied HTTP API Fetch ----------> [ Open-Meteo API ]
                          (15-minute Cashews Caching)
```

---

## 🚀 core endpoints & validation

### 1. `GET /search?q={query}`
* **Description:** Searches for cities or countries. If the query matches a country name, it immediately returns its top 20 most populated cities (Country-First strategy). Otherwise, it performs a case-insensitive search matching the city name.
* **Response Model:** `SearchResponse` containing a list of `CitySuggestion` schemas.

### 2. `GET /nearest?lat={lat}&lon={lon}`
* **Description:** Performs a local reverse-geocoding lookup. It calculates the flat Euclidean distance between the given coordinates and all cities in our database, returning the single closest city. Used for seamless client-side geolocation auto-detection.
* **Response Model:** `CitySuggestion`.

### 3. `GET /weather?lat={lat}&lon={lon}`
* **Description:** Proxies current, hourly, and daily weather forecast data from the Open-Meteo API.
* **Response Model:** `WeatherResponse`.
* **Caching:** Responses are cached in-memory with `cashews` using a **15-minute Time-To-Live (TTL)** (`@cache(ttl="15m", key="weather:{lat}:{lon}")`) to prevent API rate-limiting.

---

## 💾 database schema (`weather-data.sqlite3`)

The application database is pre-populated with indexed geographic metadata (~12MB). 

### 1. schema definitions

#### Table: `countries`
* `id` (INTEGER, PRIMARY KEY)
* `name` (TEXT, Indexed)
* `iso2` (TEXT, 2-letter country code)
* `population` (INTEGER)

#### Table: `states`
* `id` (INTEGER, PRIMARY KEY)
* `name` (TEXT)
* `state_code` (TEXT)
* `country_id` (INTEGER, FK to `countries.id`)

#### Table: `cities`
* `id` (INTEGER, PRIMARY KEY)
* `name` (TEXT, Indexed)
* `state_code` (TEXT)
* `country_code` (TEXT)
* `latitude` (REAL)
* `longitude` (REAL)
* `population` (INTEGER, Indexed - used for ranking largest cities first)

---

## ⚡ concurrency & caching architecture

* **SQLite Concurrency Gotcha:** SQLite is synchronous and blocks the thread when executing queries. To prevent blocking FastAPI's single-threaded asynchronous event loop, all database reads are offloaded to synchronous worker threads using AnyIO's thread pool pool runner (`anyio.to_thread.run_sync`).
* **Cache Strategy:** Setup is configured with a memory driver (`mem://`). Cache keys are constructed dynamically based on coordinates: `weather:{latitude}:{longitude}`. Double queries resolve directly from the local cache in **less than 0.01 seconds**.

---

## 🧪 automated integration tests

The server is backed by a 100% green Pytest suite inside `server/tests/test_api.py`.

### what is tested:
* **search endpoints:** Verifies valid searches and schema structures.
* **validation boundaries:** Confirms missing parameters trigger correct `422 Unprocessable Entity` validation errors.
* **geocoding nearest lookup:** Asserts GPS coordinates resolve to the closest real city correctly (e.g. Baku's coordinates return `Baku`).
* **in-memory cache checks:** Mocks external HTTP connections using `AsyncMock` to verify that the `cashews` cache successfully intercepts the second request and serves cached data instantly without hitting the external API.

---

## 📦 getting started

### prerequisites
* Python 3.13+
* SQLite3

### local setup
1. Navigate to the server folder:
   ```bash
   cd server
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the development server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### run unit tests
```bash
pytest tests/
```

---

## 🚀 backend deployment (render / railway)

Because `weather-data.sqlite3` is small (~12MB) and read-only, you can commit the database file directly to your Git repository! 

### Render Deployment
1. Create a new **Web Service** on Render and select your `fastapi-weather-backend` repository.
2. Render will automatically detect the Python environment.
3. Configure the **Build Command**:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure the **Start Command**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
5. Click **Deploy**. Render will generate a secure HTTPS URL (e.g. `https://my-backend.onrender.com`) which you can use as the `VITE_API_URL` for your frontend!
