import os
import json
import re
from typing import Any

import httpx


class GroqService:
    def __init__(self) -> None:
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

        # Chatbot advice now uses Gemini by default.
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.gemini_model = self._resolve_gemini_model(
            os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite-preview")
        )
        self.gemini_base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")

    def _resolve_gemini_model(self, configured_model: str) -> str:
        model = (configured_model or "").strip()
        aliases = {
            "gemini-3.1-flash-lite": "gemini-3.1-flash-lite-preview",
        }
        return aliases.get(model, model or "gemini-3.1-flash-lite-preview")

    async def transcribe(self, audio_content: bytes, filename: str, language: str = "fr") -> str:
        """Transcribe audio using Groq Whisper API"""
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is not configured")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                files = {
                    "file": (filename, audio_content, "audio/webm"),
                    "model": (None, "whisper-large-v3-turbo"),
                    "language": (None, language),
                }
                response = await client.post(
                    f"{self.groq_base_url}/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.groq_api_key}"},
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

    def _parse_advice_payload(
        self,
        raw_text: str,
        candidate_urls: set[str],
    ) -> tuple[str, str | None]:
        cleaned = (raw_text or "").strip()
        if not cleaned:
            return "", None

        # Remove optional markdown fences around JSON.
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            payload = json.loads(cleaned)
            answer = str(payload.get("answer", "")).strip()
            recommended_url = payload.get("recommended_url")
            normalized_url = str(recommended_url).strip() if isinstance(recommended_url, str) else None
            if normalized_url and normalized_url in candidate_urls:
                return answer, normalized_url
            return answer, None
        except Exception:
            pass

        # If the model did not output JSON, keep the text and try to infer a valid URL.
        found_urls = re.findall(r"https?://\S+", raw_text)
        for url in found_urls:
            normalized = url.strip().rstrip(").,;\"")
            if normalized in candidate_urls:
                return raw_text.strip(), normalized

        return raw_text.strip(), None

    async def advise(
        self,
        query: str,
        city: str,
        question: str | None,
        candidates: list[dict[str, Any]],
    ) -> tuple[str, str | None]:
        fallback_answer, fallback_url = self._fallback_advice(query, city, candidates)
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not configured for chat advice")

        simplified = []
        candidate_urls: set[str] = set()
        for item in candidates[:8]:
            payload = item.get("payload") or {}
            url_value = payload.get("url")
            if isinstance(url_value, str) and url_value.strip():
                candidate_urls.add(url_value.strip())
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
            "Reponds UNIQUEMENT avec un JSON valide au format strict: "
            '{"answer":"...","recommended_url":"..."}. '
            "Regles: 1) answer en francais, concret, 5-8 phrases max; "
            "2) recommande 1 bien principal + 1 alternative et cite les compromis; "
            "3) recommended_url doit etre exactement l'URL du bien principal et appartenir aux resultats candidats; "
            "4) si aucune URL fiable, mets recommended_url a null; "
            "5) ne retourne aucun markdown, aucun texte hors JSON."
        )

        try:
            async with httpx.AsyncClient(timeout=35.0) as client:
                response = await client.post(
                    f"{self.gemini_base_url}/models/{self.gemini_model}:generateContent",
                    params={"key": self.gemini_api_key},
                    json={
                        "system_instruction": {
                            "parts": [
                                {
                                    "text": "Tu es un conseiller immobilier francais utile, clair, et actionnable.",
                                }
                            ]
                        },
                        "contents": [
                            {
                                "role": "user",
                                "parts": [{"text": prompt}],
                            }
                        ],
                        "generationConfig": {
                            "temperature": 0.3,
                        },
                    },
                )
        except httpx.TimeoutException as exc:
            raise ValueError("Gemini request timed out") from exc
        except httpx.HTTPError as exc:
            raise ValueError(f"Gemini request failed: {exc}") from exc

        if response.status_code >= 400:
            body_preview = response.text[:400]
            raise ValueError(
                f"Gemini API error {response.status_code} with model '{self.gemini_model}': {body_preview}"
            )

        data = response.json()
        candidates_data = data.get("candidates", [])
        if not candidates_data:
            raise ValueError(f"Gemini returned no candidates: {str(data)[:400]}")

        parts = candidates_data[0].get("content", {}).get("parts", [])
        text = "\n".join(
            str(part.get("text", "")).strip()
            for part in parts
            if str(part.get("text", "")).strip()
        ).strip()

        if not text:
            raise ValueError(f"Gemini returned empty text: {str(data)[:400]}")

        parsed_answer, parsed_url = self._parse_advice_payload(text, candidate_urls)
        if not parsed_answer:
            raise ValueError(f"Gemini returned unparsable advice payload: {text[:400]}")

        return parsed_answer, parsed_url or fallback_url
