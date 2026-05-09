"""
generator.py — Sends the retrieved context + user question to an LLM.

Uses OpenRouter's unified chat completions API so the model can be
swapped in config without changing code. The prompt uses a strict
grounding instruction so the model only answers from the provided context
(reducing hallucination).
"""
import httpx
from src.config import settings
from src.rag.retriever import RetrievedChunk


SYSTEM_PROMPT = """You are Dhi, a personal knowledge assistant.
Answer the user's question using ONLY the provided context chunks.
- Cite sources by referencing the chunk title in [brackets].
- If the context does not contain enough information to answer, say so honestly.
- Be concise, clear, and insightful.
- Never make up facts that aren't in the context."""


def _build_context(chunks: list[RetrievedChunk]) -> str:
    """Formats retrieved chunks into a readable context block for the LLM."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        creators_str = ", ".join(chunk.creators) if chunk.creators else "Unknown"
        parts.append(
            f"[{i}] Title: {chunk.title}\n"
            f"    Creator: {creators_str} | Type: {chunk.source_type}\n"
            f"    Content: {chunk.text}"
        )
    return "\n\n".join(parts)


async def generate_answer(
    question: str,
    chunks: list[RetrievedChunk],
) -> str:
    """
    Send the question + retrieved context to OpenRouter and return the answer.

    Args:
        question: The user's natural language question.
        chunks:   Top-K chunks retrieved from OpenSearch.

    Returns:
        The LLM's answer string.
    """
    if not chunks:
        return "I couldn't find any relevant information in your Second Brain to answer this question."

    context = _build_context(chunks)
    user_message = f"""Context from your Second Brain:
---
{context}
---

Question: {question}"""

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "HTTP-Referer": "http://localhost:8000",
                "X-OpenRouter-Title": "Dhi Second Brain",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openrouter_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                "temperature": 0.3,  # Low temperature = more factual, less creative
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
