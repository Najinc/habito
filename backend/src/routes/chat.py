from fastapi import APIRouter, HTTPException, UploadFile, File

from src.models.chat import ChatAdviceRequest, ChatAdviceResponse
from src.services.groq import GroqService
from pydantic import BaseModel


router = APIRouter()
groq_service = GroqService()


class TranscriptionResponse(BaseModel):
    text: str


@router.post("/chat/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...), language: str = "fr") -> TranscriptionResponse:
    """Transcribe audio file using Groq Whisper API"""
    try:
        # Read the audio file
        audio_content = await file.read()
        
        # Use Groq service to transcribe
        transcription_text = await groq_service.transcribe(audio_content, file.filename, language)
        
        return TranscriptionResponse(text=transcription_text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


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
