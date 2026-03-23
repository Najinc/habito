# Habito - Moteur de recherche immobilier sémantique

Habito est un moteur de recherche d'annonces immobilières basé sur :
- des embeddings de texte,
- une recherche vectorielle Qdrant,
- un reranking lexical métier.

Le frontend affiche les résultats avec un badge de score en dégradé de couleur pour visualiser rapidement la pertinence.

## Vue d'ensemble

Stack principale :
- Frontend : Vue 3, TypeScript, Vite, Tailwind CSS
- Backend : FastAPI (Python)
- Base vectorielle : Qdrant
- Embeddings : Ollama (`nomic-embed-text`) avec fallback hash local
- Ingestion : script Python pour collecter et indexer des annonces

Flux de recherche :

1. L'utilisateur envoie une requête texte.
2. Le backend transforme la requête en vecteur (embedding).
3. Qdrant récupère les annonces proches dans l'espace vectoriel.
4. Un reranking lexical ajoute des boosts métier.
5. Les résultats sont triés par score final et renvoyés au frontend.

## Comment le scoring fonctionne

Le score final affiché est la somme de :

1. Score vectoriel Qdrant
Ce score mesure la proximité sémantique entre la requête et l'annonce.

2. Boost lexical (reranking)
Le service de reranking ajoute des points selon des règles simples :
- +0.8 : la requête normalisée complète est présente dans le texte de l'annonce
- +0.4 par token trouvé dans le texte
- +1.4 par token trouvé dans la ville

Formule simplifiée :

`score_final = score_qdrant + boosts_lexicaux`

Le tri final est décroissant sur `score_final`.

Fichiers liés au scoring :
- `backend/src/services/qdrant.py`
- `backend/src/services/rerank.py`
- `backend/src/routes/search.py`

## Dégradé de couleur du score (frontend)

Dans l'interface, chaque résultat affiche un badge `Score X.XX`.

Le badge applique un dégradé de couleur selon le score :
- score faible : teintes rouges/orangées
- score moyen : teintes jaunes
- score élevé : teintes vertes

Détail implémentation :
- le score est borné dans l'intervalle `[0, 4]` pour l'affichage,
- un hue HSL est calculé sur l'intervalle `0 -> 120`,
- un `linear-gradient(...)` est généré à partir de ce hue.

Fichier frontend concerné :
- `frontend/habito-front/src/App.vue`

## Embeddings : ce qui est utilisé

Service : `backend/src/services/ollama.py`

Comportement :
1. Appel principal Ollama : `POST /api/embed`
2. Fallback compatibilité : `POST /api/embeddings`
3. Fallback final local : embedding hash déterministe si Ollama est indisponible

Paramètres importants :
- `OLLAMA_URL` (par défaut `http://localhost:11434`)
- `OLLAMA_EMBED_MODEL` (par défaut `nomic-embed-text`)
- `EMBEDDING_DIM` (par défaut `384`)

## Recherche vectorielle : Qdrant

Service : `backend/src/services/qdrant.py`

Comportement :
- interroge la collection Qdrant avec le vecteur de la requête,
- retourne `limit` résultats avec payload.

Paramètres importants :
- `QDRANT_URL` (Docker: `http://qdrant:6333`)
- `QDRANT_COLLECTION` (par défaut `habito_ads`)
- `SEARCH_LIMIT` (par défaut `10`)

## API backend

Endpoints :
- `GET /api/health`
- `POST /api/search`

Exemple :

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "appartement 2 pieces Lille"}'
```

## Lancer le projet avec Docker

Prerequis :
- Docker
- Docker Compose
- Ollama en local avec le modele `nomic-embed-text`

Etapes :

```bash
# 1) depuis la racine du projet
docker-compose up --build -d

# 2) verifier les services
docker-compose ps
```

URLs utiles :
- Frontend : http://localhost:3000
- Backend : http://localhost:8000
- Swagger : http://localhost:8000/docs
- Qdrant dashboard : http://localhost:6333/dashboard

## Ingestion des annonces

Le dossier `ingestion/` contient le script de collecte/indexation.

Lancement docker :

```bash
docker-compose run --rm ingestion
```

Lancement local :

```bash
cd ingestion
pip install -r requirements.txt
python ingest_lbc.py
```

## Developpement local

Backend :

```bash
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

Frontend :

```bash
cd frontend/habito-front
npm install
npm run dev
```

## Structure du repository

```text
habito/
|- backend/
|  |- src/
|  |  |- routes/search.py
|  |  |- services/ollama.py
|  |  |- services/qdrant.py
|  |  |- services/rerank.py
|- frontend/habito-front/
|  |- src/App.vue
|- ingestion/
|  |- ingest_lbc.py
|- docker-compose.yml
|- README.md
```

## Notes importantes

- Le chatbot frontend a ete retire.
- La recherche reste basee sur embeddings + recherche vectorielle + reranking.
- Si Ollama est indisponible, le backend continue a fonctionner grace au fallback hash.
