from fastapi import APIRouter, HTTPException

from src.models.listing import Listing
from src.models.search import SearchRequest
from src.services.ollama import OllamaService
from src.services.qdrant import QdrantService
from src.services.rerank import RerankService


router = APIRouter()
qdrant_service = QdrantService()
ollama_service = OllamaService()
rerank_service = RerankService()


@router.post("/search", response_model=list[Listing])
async def search(req: SearchRequest) -> list[Listing]:
    try:
        vector = await ollama_service.embed(req.query)
        qdrant_results = await qdrant_service.search(vector)
        reranked = await rerank_service.rerank(req.query, qdrant_results)
        return [
            Listing(score=item["score"], payload=item.get("payload", {}))
            for item in reranked
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
