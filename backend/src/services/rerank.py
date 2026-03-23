from typing import Any
import re
import unicodedata


class RerankService:
    def _normalize(self, value: str) -> str:
        lowered = unicodedata.normalize("NFKD", value.lower())
        no_accents = "".join(c for c in lowered if not unicodedata.combining(c))
        return re.sub(r"\s+", " ", no_accents).strip()

    async def rerank(self, query: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        query_norm = self._normalize(query)
        tokens = [token for token in re.findall(r"[a-z0-9]+", query_norm) if len(token) > 1]

        rescored: list[dict[str, Any]] = []
        for item in candidates:
            payload = item.get("payload") or {}
            subject = str(payload.get("subject") or "")
            body = str(payload.get("body") or "")
            city = str(payload.get("city") or "")
            doc = str(payload.get("doc") or "")

            haystack = self._normalize(" ".join([subject, body, city, doc]))
            city_norm = self._normalize(city)

            lexical_boost = 0.0
            if query_norm and query_norm in haystack:
                lexical_boost += 0.8

            for token in tokens:
                if token in haystack:
                    lexical_boost += 0.4
                if city_norm and token in city_norm:
                    lexical_boost += 1.4

            rescored_item = dict(item)
            rescored_item["score"] = float(item.get("score", 0.0)) + lexical_boost
            rescored.append(rescored_item)

        return sorted(rescored, key=lambda item: item.get("score", 0.0), reverse=True)
