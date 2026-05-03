from fastapi import FastAPI
from src.routers import health, ask

app = FastAPI(title="arXiv Curator", version="0.1.0")

app.include_router(health.router)
app.include_router(ask.router)