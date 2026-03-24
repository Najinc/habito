from fastapi import APIRouter, HTTPException

from src.models.chat import ChatAdviceRequest, ChatAdviceResponse
from src.services.groq import GroqService


router = APIRouter()
groq_service = GroqService()


@router.post("/chat/advice", response_model=ChatAdviceResponse)
async def chat_advice(req: ChatAdviceRequest) -> ChatAdviceResponse:
    try:
        candidates = [item.model_dump() for item in req.results]
        answer, recommended_url = await groq_service.advise(
            query=req.query,
            city=req.city,
            question=req.question,
            candidates=candidates,
        )
        return ChatAdviceResponse(answer=answer, recommended_url=recommended_url)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
