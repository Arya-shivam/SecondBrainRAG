from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import health, ask, ingest

app = FastAPI(title="arXiv Curator", version="0.1.0")

# Allow Chrome Extension (and any frontend) to call our local API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For extension, wildcard is easiest, but can be restricted
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(ask.router)
app.include_router(ingest.router)