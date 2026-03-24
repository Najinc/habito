import os
import hashlib
import math
import re
import unicodedata


class OllamaService:
    def __init__(self) -> None:
        self.model_name = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-8B")
        self.default_dim = int(os.getenv("EMBEDDING_DIM", "384"))
        self.allow_hf_on_cpu = os.getenv("ALLOW_HF_ON_CPU", "false").lower() in {"1", "true", "yes", "on"}
        self._tokenizer = None
        self._model = None
        self._torch = None
        self._device = "cpu"
        self._load_attempted = False

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

    def _ensure_model(self) -> bool:
        if self._model is not None and self._tokenizer is not None and self._torch is not None:
            return True
        if self._load_attempted:
            return False

        self._load_attempted = True
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            self._torch = torch
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            if self._device == "cpu" and not self.allow_hf_on_cpu:
                print("HF embedding disabled on CPU (ALLOW_HF_ON_CPU=false): using hash embedding fast mode")
                return False

            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
            self._model = AutoModel.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                dtype=torch.float32 if self._device == "cpu" else torch.float16,
            ).to(self._device)
            self._model.eval()
            return True
        except Exception as exc:
            print(f"Embedding model load failed ({self.model_name}): {exc}")
            self._tokenizer = None
            self._model = None
            self._torch = None
            return False

    async def embed(self, text: str) -> list[float]:
        if not text.strip():
            return [0.0] * self.default_dim

        if not self._ensure_model():
            return self._hash_embed(text)

        try:
            with self._torch.no_grad():
                inputs = self._tokenizer(text, return_tensors="pt", padding=True, truncation=True).to(self._device)
                outputs = self._model(**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1)
                embedding = embeddings[0].cpu().numpy().tolist()
            
            return embedding
        except Exception as e:
            print(f"Embedding error: {e}")
            return self._hash_embed(text)
