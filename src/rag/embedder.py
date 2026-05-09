"""
embedder.py — Generates embedding vectors for text using OpenRouter's API.

OpenRouter proxies to the underlying model provider, so we can use
`nomic-ai/nomic-embed-text-v1.5` (768d) which matches our OpenSearch index.
"""
import httpx
from src.config import settings


async def embed_text(text: str) -> list[float]:
    """
    Call OpenRouter's embeddings endpoint to turn text into a 768-dim vector.
    This is called at QUERY TIME to embed the user's question.
    
    Returns:
        List of 768 floats representing the semantic meaning of the text.
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
                "input": text,
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]
