from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class AskRequest(BaseModel):
    question: str
    top_k: int = 5

class AskResponse(BaseModel):
    answer: str
    sources: list[dict]

@router.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    # Stub implementation
    return AskResponse(
        answer="Pipeline not yet connected (Phase 3).",
        sources=[]
    )
