from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from app.router import router

app = FastAPI(
    title="Weather Location Search API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, tags=["Weather Services"])
