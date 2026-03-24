from typing import Any
import os
import re
import unicodedata


class RerankService:
    def __init__(self) -> None:
        self.model_name = os.getenv("RERANKING_MODEL", "Qwen/Qwen3-Reranker-4B")
        self.allow_hf_on_cpu = os.getenv("ALLOW_HF_ON_CPU", "false").lower() in {"1", "true", "yes", "on"}
        self._tokenizer = None
        self._model = None
        self._torch = None
        self._device = "cpu"
        self._load_attempted = False

    def _normalize(self, value: str) -> str:
        lowered = unicodedata.normalize("NFKD", (value or "").lower())
        no_accents = "".join(c for c in lowered if not unicodedata.combining(c))
        return re.sub(r"\s+", " ", no_accents).strip()

    def _city_boost(self, payload: dict[str, Any], preferred_city: str | None) -> float:
        if not preferred_city:
            return 0.0

        city = self._normalize(str(payload.get("city") or ""))
        target = self._normalize(preferred_city)
        if not target:
            return 0.0
        if city == target:
            return 1.0
        if target in city or city in target:
            return 0.35
        return -0.35

    def _apply_city_heuristic(self, candidates: list[dict[str, Any]], preferred_city: str | None) -> list[dict[str, Any]]:
        rescored: list[dict[str, Any]] = []
        for item in candidates:
            payload = item.get("payload") or {}
            boosted = dict(item)
            base = float(item.get("score", 0.0))
            boosted["score"] = base + self._city_boost(payload, preferred_city)
            rescored.append(boosted)
        return sorted(rescored, key=lambda item: item.get("score", 0.0), reverse=True)

    def _ensure_model(self) -> bool:
        if self._model is not None and self._tokenizer is not None and self._torch is not None:
            return True
        if self._load_attempted:
            return False

        self._load_attempted = True
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            self._torch = torch
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            if self._device == "cpu" and not self.allow_hf_on_cpu:
                print("HF reranker disabled on CPU (ALLOW_HF_ON_CPU=false): using vector score order fast mode")
                return False

            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
            self._model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                dtype=torch.float32 if self._device == "cpu" else torch.float16,
            ).to(self._device)
            self._model.eval()
            return True
        except Exception as exc:
            print(f"Reranker model load failed ({self.model_name}): {exc}")
            self._tokenizer = None
            self._model = None
            self._torch = None
            return False

    async def rerank(self, query: str, candidates: list[dict[str, Any]], preferred_city: str | None = None) -> list[dict[str, Any]]:
        """Rerank candidates using Qwen3-Reranker-4B model."""
        if not candidates:
            return []

        if not self._ensure_model():
            return self._apply_city_heuristic(candidates, preferred_city)
        
        try:
            rescored: list[dict[str, Any]] = []
            
            with self._torch.no_grad():
                for item in candidates:
                    payload = item.get("payload") or {}
                    subject = str(payload.get("subject") or "")
                    body = str(payload.get("body") or "")
                    city = str(payload.get("city") or "")
                    
                    # Combine into a single document text
                    document = f"{subject} {body} {city}".strip()
                    
                    # Prepare input for reranker (query, document)
                    inputs = self._tokenizer(
                        query,
                        document,
                        padding=True,
                        truncation=True,
                        return_tensors="pt",
                        max_length=512
                    ).to(self._device)
                    
                    outputs = self._model(**inputs)
                    # Get logits and convert to scores
                    scores = outputs.logits.squeeze()
                    
                    if scores.dim() == 0:
                        rerank_score = float(scores.item())
                    else:
                        # For multi-class output, use the highest score
                        rerank_score = float(scores.max().item())
                    
                    rescored_item = dict(item)
                    # Combine the original vector score with the rerank score
                    original_score = float(item.get("score", 0.0))
                    rescored_item["score"] = original_score + rerank_score + self._city_boost(payload, preferred_city)
                    rescored.append(rescored_item)
            
            return sorted(rescored, key=lambda item: item.get("score", 0.0), reverse=True)
        
        except Exception as e:
            print(f"Reranking error: {e}")
            # If reranking fails, just return sorted by original score
            return self._apply_city_heuristic(candidates, preferred_city)
