from fastapi import APIRouter, HTTPException
import re
import unicodedata

from src.models.listing import Listing
from src.models.search import SearchRequest
from src.services.ingestion import IngestService
from src.services.ollama import OllamaService
from src.services.qdrant import QdrantService
from src.services.rerank import RerankService


router = APIRouter()
qdrant_service = QdrantService()
ollama_service = OllamaService()
rerank_service = RerankService()
ingest_service = IngestService()

CITY_COORDINATES: dict[str, tuple[float, float]] = {
    "paris": (48.8566, 2.3522),
    "marseille": (43.2965, 5.3698),
    "lyon": (45.7640, 4.8357),
    "toulouse": (43.6047, 1.4442),
    "nice": (43.7102, 7.2620),
    "nantes": (47.2184, -1.5536),
    "bordeaux": (44.8378, -0.5792),
    "lille": (50.6292, 3.0573),
    "rennes": (48.1173, -1.6778),
    "strasbourg": (48.5734, 7.7521),
    "montpellier": (43.6108, 3.8767),
    "cannes": (43.5524, 7.0176),
    "reims": (49.2583, 4.0317),
    "grenoble": (45.1885, 5.7245),
    "tours": (47.3941, 0.6848),
    "dijon": (47.3220, 5.0400),
    "caen": (49.1829, -0.3550),
    "angers": (47.4784, -0.5632),
    "amiens": (49.8941, 2.2958),
}


def _normalize(value: str) -> str:
    lowered = unicodedata.normalize("NFKD", (value or "").lower())
    no_accents = "".join(c for c in lowered if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", no_accents).strip()


def _city_coordinates(city: str, lat: float | None, lng: float | None) -> tuple[float, float]:
    if lat is not None and lng is not None:
        return lat, lng

    normalized_city = _normalize(city)
    if normalized_city in CITY_COORDINATES:
        return CITY_COORDINATES[normalized_city]

    # Fallback to Paris coordinates if city is unknown.
    return 48.8566, 2.3522


def _filter_by_city(items: list[dict], city: str) -> list[dict]:
    target_city = _normalize(city)
    return [
        item
        for item in items
        if _normalize(str((item.get("payload") or {}).get("city") or "")) == target_city
    ]


@router.post("/search", response_model=list[Listing])
async def search(req: SearchRequest) -> list[Listing]:
    try:
        target_city = _normalize(req.city)
        lat, lng = _city_coordinates(req.city, req.lat, req.lng)

        # If the city is not indexed yet, ingest on demand before searching.
        if req.city and not await qdrant_service.has_city(req.city):
            print(f"City '{req.city}' not indexed yet. Triggering on-demand ingestion...")
            await ingest_service.ingest_async(
                search_text=req.query,
                city=req.city,
                lat=lat,
                lng=lng,
                radius=req.radius,
            )

        vector = await ollama_service.embed(req.query)
        qdrant_results = await qdrant_service.search(vector, req.city)
        reranked = await rerank_service.rerank(req.query, qdrant_results, req.city)

        city_results = _filter_by_city(reranked, req.city)

        # Real-time scrape: if query has no result in selected city, ingest now and retry once.
        if not city_results:
            print(f"No results for query='{req.query}' in city='{req.city}'. Triggering real-time ingestion...")
            await ingest_service.ingest_async(
                search_text=req.query,
                city=req.city,
                lat=lat,
                lng=lng,
                radius=req.radius,
            )

            qdrant_results = await qdrant_service.search(vector, req.city)
            reranked = await rerank_service.rerank(req.query, qdrant_results, req.city)
            city_results = _filter_by_city(reranked, req.city)

        return [
            Listing(score=item["score"], payload=item.get("payload", {}))
            for item in city_results
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
