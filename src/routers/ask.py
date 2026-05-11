"""
ask.py — The /ask endpoint: the primary interface for querying your Second Brain.

Request → embed query → hybrid search → build context → LLM → return answer + sources.
"""
import time
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.rag.retriever import retrieve
from src.rag.generator import generate_answer

router = APIRouter()
logger = logging.getLogger(__name__)


class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    source_type: Optional[str] = None  # e.g. 'youtube', 'article', 'pdf'


class SourceDoc(BaseModel):
    document_id: str
    title: str
    creators: list[str]
    source_type: str
    chunk_text: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceDoc]
    latency_ms: int


@router.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    """
    Query your Second Brain.
    
    Runs hybrid search (BM25 + vector) over ingested knowledge,
    then sends top chunks to the LLM to generate a grounded answer.
    """
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    start = time.time()
    logger.info(f"[ask] Question: {req.question!r} | top_k={req.top_k}")

    try:
        # Step 1: Retrieve relevant chunks
        chunks = await retrieve(
            query=req.question,
            top_k=req.top_k,
            source_type=req.source_type,
        )
        logger.info(f"[ask] Retrieved {len(chunks)} chunks")

        # Step 2: Generate answer from context
        answer = await generate_answer(
            question=req.question,
            chunks=chunks,
        )

        latency_ms = int((time.time() - start) * 1000)
        logger.info(f"[ask] Done in {latency_ms}ms")

        return AskResponse(
            answer=answer,
            sources=[
                SourceDoc(
                    document_id=c.document_id,
                    title=c.title,
                    creators=c.creators,
                    source_type=c.source_type,
                    chunk_text=c.text,
                    score=round(c.score, 4),
                )
                for c in chunks
            ],
            latency_ms=latency_ms,
        )

    except Exception as e:
        logger.error(f"[ask] Failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"RAG pipeline error: {str(e)}")
