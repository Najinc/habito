import hashlib
import os
from typing import List
import math
import re
import unicodedata
import asyncio

import lbc
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


class IngestService:
    def __init__(self):
        self.qdrant = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
        )
        self.collection_name = os.getenv("QDRANT_COLLECTION", "habito_ads")
        self.vector_size = int(os.getenv("EMBEDDING_DIM", "384"))
        self.embedding_mode = os.getenv("EMBEDDING_MODE", "hash")
        self.price_min = int(os.getenv("LBC_PRICE_MIN", "500"))
        self.price_max = int(os.getenv("LBC_PRICE_MAX", "1500"))
        self.search_limit = int(os.getenv("LBC_LIMIT", "35"))

    def _normalize_text(self, text: str) -> str:
        lowered = unicodedata.normalize("NFKD", text.lower())
        ascii_text = "".join(c for c in lowered if not unicodedata.combining(c))
        return re.sub(r"\s+", " ", ascii_text).strip()

    def _hash_embed(self, text: str) -> List[float]:
        vector = [0.0] * self.vector_size
        normalized = self._normalize_text(text)
        if not normalized:
            return vector

        tokens = re.findall(r"[a-z0-9]+", normalized)
        if not tokens:
            tokens = [normalized]

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.vector_size
            sign = -1.0 if digest[4] % 2 else 1.0
            weight = 1.0 + (digest[5] / 255.0)
            vector[index] += sign * weight

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector

        return [value / norm for value in vector]

    def _build_vectors(self, docs: List[str]) -> List[List[float]]:
        if self.embedding_mode == "sentence":
            from sentence_transformers import SentenceTransformer

            embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            vectors = embedder.encode(docs, normalize_embeddings=True)
            return [vector.tolist() for vector in vectors]

        return [self._hash_embed(doc) for doc in docs]

    def _parse_float(self, value: object) -> float | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip()
        if not text:
            return None

        match = re.search(r"\d+(?:[\.,]\d+)?", text)
        if not match:
            return None

        try:
            return float(match.group(0).replace(",", "."))
        except ValueError:
            return None

    def _extract_square(self, ad, subject: str | None, body: str | None) -> float | None:
        direct = self._parse_float(getattr(ad, "square", None))
        if direct is not None:
            return direct

        text = f"{subject or ''} {body or ''}"
        match = re.search(
            r"(\d{1,4}(?:[\.,]\d+)?)\s*m[^0-9]{0,2}(?:2|²)\b", self._normalize_text(text)
        )
        if not match:
            return None
        return self._parse_float(match.group(1))

    def _extract_rooms(self, ad, subject: str | None, body: str | None) -> int | None:
        direct = self._parse_float(getattr(ad, "rooms", None))
        if direct is not None:
            return int(round(direct))

        text = self._normalize_text(f"{subject or ''} {body or ''}")
        match = re.search(r"\b(\d{1,2})\s*p\w*", text)
        if not match:
            return None
        return int(round(self._parse_float(match.group(1)) or 0))

    def _make_doc(self, ad) -> str:
        subject = getattr(ad, "subject", None)
        body = getattr(ad, "body", None)
        square = self._extract_square(ad, subject, body)
        rooms = self._extract_rooms(ad, subject, body)

        parts = [
            f"Titre: {subject or ''}",
            f"Description: {body or ''}",
            f"Prix: {getattr(ad, 'price', '') or ''} euros",
            f"Ville: {getattr(ad, 'city', '') or ''}",
            f"Surface: {square or ''} m2",
            f"Pièces: {rooms or ''}",
            f"URL: {getattr(ad, 'url', '') or ''}",
        ]
        return "\n".join(parts)

    def _stable_id(self, ad) -> int:
        raw = str(getattr(ad, "list_id", None) or getattr(ad, "url", ""))
        digest = hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]
        return int(digest, 16)

    def _ad_payload(self, ad, doc: str, city: str) -> dict:
        subject = getattr(ad, "subject", None)
        body = getattr(ad, "body", None)
        square_value = self._extract_square(ad, subject, body)
        rooms_value = self._extract_rooms(ad, subject, body)

        # Extract first image URL
        image_url = None
        images = getattr(ad, "images", None) or []
        if images and len(images) > 0:
            image_url = images[0]

        return {
            "ad_id": getattr(ad, "list_id", None),
            "subject": subject,
            "body": body,
            "price": getattr(ad, "price", None),
            "city": city,
            "square": square_value,
            "rooms": rooms_value,
            "url": getattr(ad, "url", None),
            "image_url": image_url,
            "doc": doc,
            "source": "lbc",
        }

    def _ensure_collection(self):
        try:
            collections = self.qdrant.get_collections().collections
            names = [c.name for c in collections]
            if self.collection_name not in names:
                self.qdrant.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE,
                    ),
                )
        except Exception:
            pass

    async def ingest_async(
        self,
        search_text: str,
        city: str,
        lat: float,
        lng: float,
        radius: int,
    ) -> int:
        """
        Async ingestion with custom parameters.
        Returns number of points ingested.
        """
        self._ensure_collection()

        try:
            client = lbc.Client()
            location = lbc.City(lat=lat, lng=lng, radius=radius, city=city)

            result = client.search(
                text=search_text,
                locations=[location],
                page=1,
                limit=self.search_limit,
                sort=lbc.Sort.NEWEST,
                ad_type=lbc.AdType.OFFER,
                category=lbc.Category.IMMOBILIER,
                price=[self.price_min, self.price_max],
            )

            if not result.ads:
                return 0

            # Build documents and vectors
            docs = [self._make_doc(ad) for ad in result.ads]
            vectors = self._build_vectors(docs)

            # Create points
            points = []
            for ad, doc, vector in zip(result.ads, docs, vectors):
                points.append(
                    PointStruct(
                        id=self._stable_id(ad),
                        vector=vector,
                        payload=self._ad_payload(ad, doc, city),
                    )
                )

            # Upsert to Qdrant
            self.qdrant.upsert(
                collection_name=self.collection_name,
                points=points,
            )

            return len(points)

        except Exception as e:
            print(f"Erreur ingestion: {e}")
            return 0
