import os
from typing import Any

import httpx


class QdrantService:
    def __init__(self) -> None:
        self.base_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.collection = os.getenv("QDRANT_COLLECTION", "habito_ads")
        self.limit = int(os.getenv("SEARCH_LIMIT", "10"))

    async def search(self, vector: list[float]) -> list[dict[str, Any]]:
        endpoint = f"{self.base_url}/collections/{self.collection}/points/search"
        payload = {
            "vector": vector,
            "limit": self.limit,
            "with_payload": True,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception:
            return []

        return data.get("result", [])
