import hashlib
import os
from typing import List
import math
import re
import unicodedata
import json
from pathlib import Path

import lbc
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

COLLECTION_NAME = "habito_ads"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-8B")

qdrant = QdrantClient(
    host=os.getenv("QDRANT_HOST", "localhost"),
    port=int(os.getenv("QDRANT_PORT", "6333")),
)

SEARCH_TEXT = os.getenv("LBC_TEXT", "appartement")
SEARCH_CITY = os.getenv("LBC_CITY", "Paris")
SEARCH_LAT = float(os.getenv("LBC_LAT", "48.8566"))
SEARCH_LNG = float(os.getenv("LBC_LNG", "2.3522"))
SEARCH_RADIUS = int(os.getenv("LBC_RADIUS", "10000"))
SEARCH_PAGE = int(os.getenv("LBC_PAGE", "1"))
SEARCH_LIMIT = int(os.getenv("LBC_LIMIT", "35"))
SEARCH_PRICE_MIN = int(os.getenv("LBC_PRICE_MIN", "500"))
SEARCH_PRICE_MAX = int(os.getenv("LBC_PRICE_MAX", "1500"))
PROGRESSIVE_MODE = os.getenv("LBC_PROGRESSIVE", "false").lower() in {"1", "true", "yes", "on"}
MAX_PAGES_PER_RUN = max(1, int(os.getenv("LBC_MAX_PAGES", "1")))
STATE_FILE = Path(os.getenv("LBC_STATE_FILE", "./.ingest_state.json"))
DEFAULT_LOCATIONS = os.getenv(
    "LBC_LOCATIONS",
    "Paris:48.8566:2.3522;Lille:50.6292:3.0573;Reims:49.2583:4.0317",
)

DEFAULT_EMBED_DIM = int(os.getenv("EMBEDDING_DIM", "384"))
torch_lib = None
tokenizer = None
embedding_model = None
device = "cpu"
_model_load_attempted = False


def ensure_embedding_model() -> bool:
    global torch_lib, tokenizer, embedding_model, device, _model_load_attempted
    if tokenizer is not None and embedding_model is not None and torch_lib is not None:
        return True
    if _model_load_attempted:
        return False

    _model_load_attempted = True
    try:
        import torch
        from transformers import AutoModel, AutoTokenizer

        torch_lib = torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL, trust_remote_code=True)
        embedding_model = AutoModel.from_pretrained(
            EMBEDDING_MODEL,
            trust_remote_code=True,
            torch_dtype=torch.float32 if device == "cpu" else torch.float16,
        ).to(device)
        embedding_model.eval()
        return True
    except Exception as exc:
        print(f"Embedding model load failed ({EMBEDDING_MODEL}): {exc}")
        torch_lib = None
        tokenizer = None
        embedding_model = None
        return False


def normalize_text(text: str) -> str:
    lowered = unicodedata.normalize("NFKD", text.lower())
    ascii_text = "".join(c for c in lowered if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", ascii_text).strip()


def qwen_embed(text: str) -> List[float]:
    """Generate embedding using Qwen3-Embedding-8B model."""
    if not text.strip():
        return [0.0] * DEFAULT_EMBED_DIM

    if not ensure_embedding_model():
        return [0.0] * DEFAULT_EMBED_DIM
    
    try:
        with torch_lib.no_grad():
            inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True).to(device)
            outputs = embedding_model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1)
            embedding = embeddings[0].cpu().numpy().tolist()
        return embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return [0.0] * DEFAULT_EMBED_DIM


def configured_locations() -> list[tuple[str, lbc.City]]:
    locations: list[tuple[str, lbc.City]] = []
    for entry in DEFAULT_LOCATIONS.split(";"):
        value = entry.strip()
        if not value:
            continue

        try:
            city, lat, lng = [part.strip() for part in value.split(":")]
            locations.append(
                (
                    city,
                    lbc.City(
                        lat=float(lat),
                        lng=float(lng),
                        radius=SEARCH_RADIUS,
                        city=city,
                    ),
                )
            )
        except Exception:
            continue

    if locations:
        return locations

    return [
        (
            SEARCH_CITY,
            lbc.City(
                lat=SEARCH_LAT,
                lng=SEARCH_LNG,
                radius=SEARCH_RADIUS,
                city=SEARCH_CITY,
            ),
        )
    ]


def extract_city(ad, doc: str, requested_city: str) -> str | None:
    direct_city = (
        getattr(ad, "city", None)
        or getattr(getattr(ad, "location", None), "city", None)
        or getattr(getattr(ad, "location", None), "city_label", None)
    )
    if direct_city:
        return str(direct_city)

    normalized_doc = normalize_text(doc)
    for city_name, _ in configured_locations():
        if normalize_text(city_name) in normalized_doc:
            return city_name

    return requested_city or None


def parse_float(value: object) -> float | None:
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


def parse_int(value: object) -> int | None:
    parsed = parse_float(value)
    if parsed is None:
        return None
    return int(round(parsed))


def attribute_lookup(ad, keys: list[str]) -> object | None:
    normalized_keys = {normalize_text(key) for key in keys}
    for attribute in getattr(ad, "attributes", []) or []:
        attr_key = normalize_text(str(getattr(attribute, "key", "") or ""))
        attr_key_label = normalize_text(str(getattr(attribute, "key_label", "") or ""))
        if attr_key in normalized_keys or attr_key_label in normalized_keys:
            value_label = getattr(attribute, "value_label", None)
            value = getattr(attribute, "value", None)
            values_label = getattr(attribute, "values_label", None)
            values = getattr(attribute, "values", None)
            return value_label or value or (values_label[0] if values_label else None) or (values[0] if values else None)
    return None


def extract_square(ad, subject: str | None, body: str | None) -> float | None:
    direct = parse_float(getattr(ad, "square", None))
    if direct is not None:
        return direct

    attr_value = attribute_lookup(ad, ["square", "surface", "surface habitable"])
    parsed_attr = parse_float(attr_value)
    if parsed_attr is not None:
        return parsed_attr

    text = f"{subject or ''} {body or ''}"
    match = re.search(r"(\d{1,4}(?:[\.,]\d+)?)\s*m[^0-9]{0,2}(?:2|²)\b", normalize_text(text))
    if not match:
        return None
    return parse_float(match.group(1))


def extract_rooms(ad, subject: str | None, body: str | None) -> int | None:
    direct = parse_int(getattr(ad, "rooms", None))
    if direct is not None:
        return direct

    attr_value = attribute_lookup(ad, ["rooms", "pieces", "piece"])
    parsed_attr = parse_int(attr_value)
    if parsed_attr is not None:
        return parsed_attr

    text = normalize_text(f"{subject or ''} {body or ''}")
    match = re.search(r"\b(\d{1,2})\s*p\w*", text)
    if not match:
        return None
    return parse_int(match.group(1))


def load_state() -> dict:
    if not PROGRESSIVE_MODE:
        return {"cities": {}}
    if not STATE_FILE.exists():
        return {"cities": {}}

    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"cities": {}}


def save_state(state: dict) -> None:
    if not PROGRESSIVE_MODE:
        return
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_collection():
    collections = qdrant.get_collections().collections
    names = [c.name for c in collections]
    if COLLECTION_NAME not in names:
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=DEFAULT_EMBED_DIM,
                distance=Distance.COSINE,
            ),
        )


def build_vectors(docs: List[str]) -> List[List[float]]:
    return [qwen_embed(doc) for doc in docs]


def make_doc(ad) -> str:
    subject = getattr(ad, "subject", None)
    body = getattr(ad, "body", None)
    square = extract_square(ad, subject, body)
    rooms = extract_rooms(ad, subject, body)

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


def stable_id(ad) -> int:
    raw = str(getattr(ad, "list_id", None) or getattr(ad, "url", ""))
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]
    return int(digest, 16)


def ad_payload(ad, doc: str, requested_city: str) -> dict:
    city_value = extract_city(ad, doc, requested_city)
    subject = getattr(ad, "subject", None)
    body = getattr(ad, "body", None)
    square_value = extract_square(ad, subject, body)
    rooms_value = extract_rooms(ad, subject, body)
    
    # Extract first image URL from images list
    image_url = None
    images = getattr(ad, "images", None) or []
    if images and len(images) > 0:
        image_url = images[0]

    return {
        "ad_id": getattr(ad, "list_id", None),
        "subject": subject,
        "body": body,
        "price": getattr(ad, "price", None),
        "city": city_value,
        "square": square_value,
        "rooms": rooms_value,
        "url": getattr(ad, "url", None),
        "image_url": image_url,
        "doc": doc,
        "source": "lbc",
    }


def fetch_ads(state: dict) -> tuple[list[tuple[object, str]], dict]:
    client = lbc.Client()
    locations = configured_locations()
    ads_with_city: list[tuple[object, str]] = []
    seen_urls: set[str] = set()

    if "cities" not in state or not isinstance(state.get("cities"), dict):
        state["cities"] = {}

    for city_name, location in locations:
        city_state = state["cities"].get(city_name, {})
        city_start_page = int(city_state.get("next_page", SEARCH_PAGE)) if PROGRESSIVE_MODE else SEARCH_PAGE
        pages_to_fetch = MAX_PAGES_PER_RUN if PROGRESSIVE_MODE else 1
        last_page_with_ads = city_start_page - 1

        for page in range(city_start_page, city_start_page + pages_to_fetch):
            try:
                result = client.search(
                    text=SEARCH_TEXT,
                    locations=[location],
                    page=page,
                    limit=SEARCH_LIMIT,
                    sort=lbc.Sort.NEWEST,
                    ad_type=lbc.AdType.OFFER,
                    category=lbc.Category.IMMOBILIER,
                    price=[SEARCH_PRICE_MIN, SEARCH_PRICE_MAX],
                )
            except Exception as exc:
                raise RuntimeError(
                    "Erreur scraping Leboncoin via lbc. "
                    "Vérifie la connectivité/rate-limit (403 Datadome possible)."
                ) from exc

            if not result.ads:
                if PROGRESSIVE_MODE:
                    state["cities"][city_name] = {"next_page": SEARCH_PAGE}
                break

            last_page_with_ads = page

            for ad in result.ads:
                ad_url = str(getattr(ad, "url", "") or "")
                if ad_url and ad_url in seen_urls:
                    continue
                if ad_url:
                    seen_urls.add(ad_url)
                ads_with_city.append((ad, city_name))

            if len(result.ads) < SEARCH_LIMIT:
                if PROGRESSIVE_MODE:
                    state["cities"][city_name] = {"next_page": SEARCH_PAGE}
                break
        else:
            if PROGRESSIVE_MODE:
                state["cities"][city_name] = {"next_page": last_page_with_ads + 1}

    return ads_with_city, state


def ingest():
    ensure_collection()
    state = load_state()
    ads_with_city, state = fetch_ads(state)

    if not ads_with_city:
        print("Aucune annonce récupérée depuis Leboncoin")
        save_state(state)
        return

    docs: List[str] = [make_doc(ad) for ad, _ in ads_with_city]
    vectors = build_vectors(docs)

    points = []
    for (ad, requested_city), doc, vector in zip(ads_with_city, docs, vectors):
        points.append(
            PointStruct(
                id=stable_id(ad),
                vector=vector,
                payload=ad_payload(ad, doc, requested_city),
            )
        )

    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    save_state(state)

    print(f"{len(points)} annonces insérées / mises à jour dans Qdrant")


if __name__ == "__main__":
    ingest()