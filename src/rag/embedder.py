"""
embedder.py — Generates embedding vectors for text using OpenRouter's API.

Uses nvidia/llama-nemotron-embed-vl-1b-v2:free (2048-dim) via OpenRouter.
This model requires input as a list of content objects:
  [{"type": "text", "text": "..."}]
"""
import logging
import httpx
from src.config import settings

logger = logging.getLogger(__name__)


def _make_content(text: str) -> list:
    """Wrap plain text into the content-object format required by the nvidia embed model."""
    return [{"type": "text", "text": text}]


async def embed_text(text: str) -> list[float]:
    """
    Embed a single text string into a 2048-dim vector via OpenRouter.
    Called at QUERY TIME to embed the user's question.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/embeddings",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.embed_model,
                "input": [_make_content(text)],
                "encoding_format": "float",
            },
        )
        if response.status_code != 200:
            logger.error(f"Embedder error {response.status_code}: {response.text}")
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed multiple texts in a single API call.
    Batching prevents 429 rate-limit errors and is cheaper per-token.
    """
    if not texts:
        return []

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/embeddings",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.embed_model,
                "input": [_make_content(t) for t in texts],
                "encoding_format": "float",
            },
        )
        if response.status_code != 200:
            logger.error(f"Batch embedder error {response.status_code}: {response.text}")
        response.raise_for_status()
        data = response.json()

        # Sort by index (OpenRouter may return items out of order)
        embeddings = sorted(data.get("data", []), key=lambda x: x["index"])
        return [item["embedding"] for item in embeddings]
