import os
import hashlib
import math
import re
import unicodedata

import httpx


class OllamaService:
    def __init__(self) -> None:
        self.base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        self.default_dim = int(os.getenv("EMBEDDING_DIM", "384"))

    def _normalize_text(self, text: str) -> str:
        lowered = unicodedata.normalize("NFKD", text.lower())
        ascii_text = "".join(c for c in lowered if not unicodedata.combining(c))
        return re.sub(r"\s+", " ", ascii_text).strip()

    def _hash_embed(self, text: str) -> list[float]:
        vector = [0.0] * self.default_dim
        normalized = self._normalize_text(text)
        if not normalized:
            return vector

        tokens = re.findall(r"[a-z0-9]+", normalized)
        if not tokens:
            tokens = [normalized]

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.default_dim
            sign = -1.0 if digest[4] % 2 else 1.0
            weight = 1.0 + (digest[5] / 255.0)
            vector[index] += sign * weight

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector

        return [value / norm for value in vector]

    async def embed(self, text: str) -> list[float]:
        if not text.strip():
            return [0.0] * self.default_dim

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/embed",
                    json={"model": self.model, "input": text},
                )

                if response.status_code >= 400:
                    fallback = await client.post(
                        f"{self.base_url}/api/embeddings",
                        json={"model": self.model, "prompt": text},
                    )
                    fallback.raise_for_status()
                    fallback_data = fallback.json()
                    return fallback_data.get("embedding", self._hash_embed(text))

                data = response.json()
                embeddings = data.get("embeddings", [])
                if embeddings and isinstance(embeddings, list):
                    first_vector = embeddings[0]
                    if isinstance(first_vector, list):
                        return first_vector
        except Exception:
            return self._hash_embed(text)

        return self._hash_embed(text)
