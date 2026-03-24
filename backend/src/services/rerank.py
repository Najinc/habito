from typing import Any
import os
import re
import unicodedata
import time
import math


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

    def _date_boost(self, payload: dict[str, Any]) -> float:
        """Boost recent listings higher. Max boost of 0.5 for ads from today."""
        pub_date = payload.get("first_publication_date")
        if not pub_date:
            return 0.0
        
        try:
            current_time = time.time()
            age_seconds = current_time - pub_date
            age_days = age_seconds / (24 * 3600)
            
            # Exponential decay: newer = higher boost
            # Today: 0.5, 7 days: 0.25, 30 days: 0.05, 90+ days: 0.0
            boost = 0.5 * math.exp(-age_days / 30.0)
            return round(max(0.0, min(0.5, boost)), 3)
        except Exception:
            return 0.0

    def _image_boost(self, payload: dict[str, Any]) -> float:
        """Boost listings with more photos. Max boost of 0.3 for 8+ photos."""
        images = payload.get("images") or []
        num_images = len(images) if isinstance(images, list) else 0
        
        if num_images == 0:
            return 0.0
        
        # 1-3 photos: 0.05, 4-7 photos: 0.15, 8+ photos: 0.3
        if num_images >= 8:
            return 0.3
        elif num_images >= 4:
            return 0.15
        else:
            return 0.05

    def _verified_boost(self, payload: dict[str, Any]) -> float:
        """Boost verified/professional listings. Check if listing appears professional."""
        # In real scenario, this would come from LBC metadata
        # For now: presence of many images + complete details suggests verified/pro
        images = payload.get("images") or []
        num_images = len(images) if isinstance(images, list) else 0
        price = payload.get("price")
        square = payload.get("square")
        
        # More than 4 images + both price and square = likely pro/verified
        if num_images >= 4 and price and square:
            return 0.1
        return 0.0

    def _apply_city_heuristic(self, candidates: list[dict[str, Any]], preferred_city: str | None) -> list[dict[str, Any]]:
        rescored: list[dict[str, Any]] = []
        for item in candidates:
            payload = item.get("payload") or {}
            boosted = dict(item)
            
            base_score = float(item.get("score", 0.0))
            city_boost = self._city_boost(payload, preferred_city)
            date_boost = self._date_boost(payload)
            image_boost = self._image_boost(payload)
            verified_boost = self._verified_boost(payload)
            
            total_boost = city_boost + date_boost + image_boost + verified_boost
            final_score = base_score + total_boost
            
            # Store score breakdown in payload
            if "payload" not in boosted:
                boosted["payload"] = {}
            boosted["payload"]["score_breakdown"] = {
                "vector_score": round(base_score, 3),
                "city_boost": round(city_boost, 3),
                "date_boost": round(date_boost, 3),
                "image_boost": round(image_boost, 3),
                "verified_boost": round(verified_boost, 3),
                "total_score": round(final_score, 3),
            }
            
            boosted["score"] = final_score
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
        """Rerank candidates using Qwen3-Reranker-4B model with additional boosts."""
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
                    
                    # Calculate all boosts
                    vector_score = float(item.get("score", 0.0))
                    city_boost = self._city_boost(payload, preferred_city)
                    date_boost = self._date_boost(payload)
                    image_boost = self._image_boost(payload)
                    verified_boost = self._verified_boost(payload)
                    
                    # Final score combines vector + rerank + all boosts
                    total_boosts = city_boost + date_boost + image_boost + verified_boost
                    final_score = vector_score + rerank_score + total_boosts
                    
                    # Store score breakdown in payload
                    rescored_item = dict(item)
                    if "payload" not in rescored_item:
                        rescored_item["payload"] = {}
                    rescored_item["payload"]["score_breakdown"] = {
                        "vector_score": round(vector_score, 3),
                        "rerank_score": round(rerank_score, 3),
                        "city_boost": round(city_boost, 3),
                        "date_boost": round(date_boost, 3),
                        "image_boost": round(image_boost, 3),
                        "verified_boost": round(verified_boost, 3),
                        "total_score": round(final_score, 3),
                    }
                    
                    rescored_item["score"] = final_score
                    rescored.append(rescored_item)
            
            return sorted(rescored, key=lambda item: item.get("score", 0.0), reverse=True)
        
        except Exception as e:
            print(f"Reranking error: {e}")
            # If reranking fails, fall back to heuristic with all boosts
            return self._apply_city_heuristic(candidates, preferred_city)
