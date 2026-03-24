import os
from typing import Any

import httpx


class GroqService:
    def __init__(self) -> None:
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    async def transcribe(self, audio_content: bytes, filename: str, language: str = "fr") -> str:
        """Transcribe audio using Groq Whisper API"""
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not configured")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                files = {
                    "file": (filename, audio_content, "audio/webm"),
                    "model": (None, "whisper-large-v3-turbo"),
                    "language": (None, language),
                }
                response = await client.post(
                    f"{self.base_url}/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    files=files,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("text", "")
        except Exception as e:
            raise ValueError(f"Transcription failed: {str(e)}") from e

    def _fallback_advice(self, query: str, city: str, candidates: list[dict[str, Any]]) -> tuple[str, str | None]:
        if not candidates:
            return (
                f"Je n'ai pas encore trouvé d'annonce pertinente pour '{query}' à {city}. "
                "Essaie d'élargir les filtres (prix/surface) ou de reformuler la recherche.",
                None,
            )

        top = candidates[0]
        payload = top.get("payload") or {}
        subject = str(payload.get("subject") or "Annonce")
        price = payload.get("price")
        square = payload.get("square")
        rooms = payload.get("rooms")
        url = payload.get("url")

        details: list[str] = []
        if price is not None:
            details.append(f"prix {price} EUR")
        if square is not None:
            details.append(f"surface {square} m2")
        if rooms is not None:
            details.append(f"{rooms} piece(s)")

        detail_text = ", ".join(details) if details else "infos partielles"
        answer = (
            f"Mon conseil: commence par '{subject}' à {city}. "
            f"C'est le meilleur score actuel ({top.get('score', 0.0):.2f}) pour ta recherche '{query}', avec {detail_text}. "
            "Compare ensuite avec les 2-3 annonces suivantes pour valider le compromis prix/surface/localisation."
        )
        return answer, str(url) if isinstance(url, str) else None

    async def advise(
        self,
        query: str,
        city: str,
        question: str | None,
        candidates: list[dict[str, Any]],
    ) -> tuple[str, str | None]:
        fallback_answer, fallback_url = self._fallback_advice(query, city, candidates)
        if not self.api_key:
            return fallback_answer, fallback_url

        simplified = []
        for item in candidates[:8]:
            payload = item.get("payload") or {}
            simplified.append(
                {
                    "score": float(item.get("score", 0.0)),
                    "subject": payload.get("subject"),
                    "price": payload.get("price"),
                    "city": payload.get("city"),
                    "square": payload.get("square"),
                    "rooms": payload.get("rooms"),
                    "url": payload.get("url"),
                }
            )

        user_question = question or "Quel est le meilleur bien pour moi et pourquoi ?"
        prompt = (
            f"Recherche utilisateur: {query}\n"
            f"Ville: {city}\n"
            f"Question: {user_question}\n"
            f"Resultats candidats: {simplified}\n"
            "Donne une reponse en francais, concrete, en 5-8 phrases max. "
            "Recommande 1 bien principal + 1 alternative, explique pourquoi, et cite les compromis."
        )

        try:
            async with httpx.AsyncClient(timeout=35.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "temperature": 0.3,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Tu es un conseiller immobilier francais utile, clair, et actionnable.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                    },
                )
                response.raise_for_status()
                data = response.json()
                choices = data.get("choices", [])
                if choices:
                    text = choices[0].get("message", {}).get("content", "").strip()
                    if text:
                        return text, fallback_url
        except Exception:
            pass

        return fallback_answer, fallback_url
