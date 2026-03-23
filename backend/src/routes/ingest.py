import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from src.services.ingestion import IngestService


router = APIRouter()
ingest_service = IngestService()


class IngestRequest(BaseModel):
    search_text: str
    city: str
    lat: float = 48.8566
    lng: float = 2.3522
    radius: int = 10000


class IngestResponse(BaseModel):
    status: str
    message: str
    points_count: int = 0


@router.post("/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest, background_tasks: BackgroundTasks) -> IngestResponse:
    """
    Trigger ingestion with custom search parameters.
    Returns immediately while ingestion happens in background.
    """
    try:
        # Schedule ingestion in background
        background_tasks.add_task(
            ingest_service.ingest_async,
            search_text=req.search_text,
            city=req.city,
            lat=req.lat,
            lng=req.lng,
            radius=req.radius,
        )

        return IngestResponse(
            status="queued",
            message=f"Ingestion lancée pour '{req.search_text}' à {req.city}",
            points_count=0,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
