from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import ChatRequest, ChatResponse
from app.services.ai_chat_service import chat_with_openai_compatible

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    reply = chat_with_openai_compatible(
        db,
        message=payload.message,
        history=[x.model_dump() for x in payload.history],
    )
    return {"reply": reply}
