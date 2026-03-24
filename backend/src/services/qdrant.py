import os
from typing import Any

import httpx


class QdrantService:
    def __init__(self) -> None:
        self.base_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.collection = os.getenv("QDRANT_COLLECTION", "habito_ads")
        self.limit = int(os.getenv("SEARCH_LIMIT", "10"))

    async def search(self, vector: list[float], city: str | None = None) -> list[dict[str, Any]]:
        endpoint = f"{self.base_url}/collections/{self.collection}/points/search"
        payload = {
            "vector": vector,
            "limit": self.limit,
            "with_payload": True,
        }

        city_value = (city or "").strip()
        if city_value:
            payload["filter"] = {
                "must": [
                    {
                        "key": "city",
                        "match": {
                            "value": city_value,
                        },
                    }
                ]
            }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception:
            return []

        return data.get("result", [])

    async def has_city(self, city: str) -> bool:
        endpoint = f"{self.base_url}/collections/{self.collection}/points/scroll"
        city_value = (city or "").strip()
        if not city_value:
            return False

        # Try a couple of common casings to avoid case mismatch issues.
        candidates = [city_value, city_value.title()]
        tested: set[str] = set()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for candidate in candidates:
                    if candidate in tested:
                        continue
                    tested.add(candidate)

                    payload = {
                        "filter": {
                            "must": [
                                {
                                    "key": "city",
                                    "match": {
                                        "value": candidate,
                                    },
                                }
                            ]
                        },
                        "limit": 1,
                        "with_payload": False,
                        "with_vector": False,
                    }
                    response = await client.post(endpoint, json=payload)
                    if response.status_code >= 400:
                        continue

                    data = response.json().get("result", {})
                    points = data.get("points", [])
                    if points:
                        return True
        except Exception:
            return False

        return False
