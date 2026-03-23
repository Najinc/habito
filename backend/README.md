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
- `OLLAMA_URL` (défaut: `http://localhost:11434`)
- `OLLAMA_EMBED_MODEL` (défaut: `nomic-embed-text`)
- `EMBEDDING_DIM` (défaut: `384`)

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

Note: si Ollama n'est pas accessible, `POST /api/search` retourne une liste vide au lieu d'une erreur.