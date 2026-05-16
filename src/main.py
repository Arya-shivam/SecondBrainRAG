import sys
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Force unbuffered stdout so print() appears immediately in terminal
os.environ["PYTHONUNBUFFERED"] = "1"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.routers import health, ask, ingest

# Configure root logger BEFORE anything else
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,  # Override any existing config from submodules
)

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")