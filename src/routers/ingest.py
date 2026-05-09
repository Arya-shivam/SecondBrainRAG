from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import logging

from src.ingest.universal_ingest import ingest

router = APIRouter()
logger = logging.getLogger(__name__)

class IngestRequest(BaseModel):
    url: str
    tags: Optional[List[str]] = ["extension-capture"]
    folder: Optional[str] = None  # Custom vault subfolder e.g. 'research', 'work'

class IngestResponse(BaseModel):
    status: str
    message: str

def run_ingestion_task(url: str, tags: List[str], folder: Optional[str] = None):
    try:
        logger.info(f"Background task starting ingestion for: {url}")
        ingest(url, tags=tags, folder=folder)
        logger.info(f"Successfully ingested: {url}")
    except Exception as e:
        logger.error(f"Failed to ingest {url}: {str(e)}")

@router.post("/api/ingest", response_model=IngestResponse)
async def api_ingest(req: IngestRequest, background_tasks: BackgroundTasks):
    """
    Ingest a URL from the Chrome Extension or Telegram Bot.
    Runs the ingestion in the background so the UI doesn't hang.
    """
    if not req.url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL format")
        
    # We pass it to background tasks because downloading/parsing might take a few seconds
    background_tasks.add_task(run_ingestion_task, req.url, req.tags, req.folder)
    
    return IngestResponse(
        status="success", 
        message=f"Started ingestion for {req.url}"
    )
