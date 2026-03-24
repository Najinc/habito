# Habito Backend (Python)

## Installation

```bash
pip install -r requirements.txt
```

## Lancement

```bash
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

## Variables d'environnement

- `QDRANT_URL` (défaut: `http://localhost:6333`)
- `QDRANT_COLLECTION` (défaut: `habito_ads`)
- `SEARCH_LIMIT` (défaut: `10`)
- `EMBEDDING_MODEL` (défaut: `Qwen/Qwen3-Embedding-8B`)
- `RERANKING_MODEL` (défaut: `Qwen/Qwen3-Reranker-4B`)

## Endpoints

- `GET /api/health`
- `POST /api/search`

## Docker

Depuis la racine du workspace:

```bash
docker compose up --build -d backend
```

Pour lancer backend + Qdrant:

```bash
docker compose up --build -d
```

Arrêt:

```bash
docker compose down
```