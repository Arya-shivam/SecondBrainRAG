import sys
import traceback
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import logging
import httpx

from src.ingest.universal_ingest import ingest

router = APIRouter()
logger = logging.getLogger(__name__)

class IngestRequest(BaseModel):
    url: str
    tags: Optional[List[str]] = ["extension-capture"]
    folder: Optional[str] = None  # Custom vault subfolder e.g. 'research', 'work'
    # Optional: Telegram callback so the background task can report back
    telegram_chat_id: Optional[int] = None
    telegram_bot_token: Optional[str] = None

class IngestResponse(BaseModel):
    status: str
    message: str

def _send_telegram_message(bot_token: str, chat_id: int, text: str):
    """Fire-and-forget helper to send a message back to the Telegram user."""
    try:
        resp = httpx.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=10.0,
        )
        print(f"[TELEGRAM-CALLBACK] status={resp.status_code}", flush=True)
    except Exception as e:
        print(f"[TELEGRAM-CALLBACK] FAILED: {e}", flush=True)


def run_ingestion_task(
    url: str,
    tags: List[str],
    folder: Optional[str] = None,
    telegram_chat_id: Optional[int] = None,
    telegram_bot_token: Optional[str] = None,
):
    print(f"[INGESTION] >>> Starting background task for: {url}", flush=True)
    try:
        saved_path = ingest(url, tags=tags, folder=folder)
        print(f"[INGESTION] SUCCESS: {saved_path}", flush=True)
        if telegram_chat_id and telegram_bot_token:
            _send_telegram_message(
                telegram_bot_token,
                telegram_chat_id,
                f"✅ *Ingestion complete!*\n\n"
                f"🗂 Saved to vault:\n`{saved_path.name}`\n\n"
                f"📁 Folder: `{saved_path.parent.name}`",
            )
    except Exception as e:
        print(f"[INGESTION] FAILED: {url}", flush=True)
        traceback.print_exc()
        sys.stdout.flush()
        if telegram_chat_id and telegram_bot_token:
            _send_telegram_message(
                telegram_bot_token,
                telegram_chat_id,
                f"❌ *Ingestion failed!*\n\nURL: `{url}`\n\nError: `{str(e)}`",
            )

@router.post("/api/ingest", response_model=IngestResponse)
async def api_ingest(req: IngestRequest, background_tasks: BackgroundTasks):
    """
    Ingest a URL from the Chrome Extension or Telegram Bot.
    Runs the ingestion in the background so the UI doesn't hang.
    """
    print(f"[API] Received ingest request: {req.url} (chat_id={req.telegram_chat_id})", flush=True)
    
    if not req.url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL format")
        
    # We pass it to background tasks because downloading/parsing might take a few seconds
    background_tasks.add_task(
        run_ingestion_task,
        req.url,
        req.tags,
        req.folder,
        req.telegram_chat_id,
        req.telegram_bot_token,
    )
    
    return IngestResponse(
        status="success", 
        message=f"Started ingestion for {req.url}"
    )
