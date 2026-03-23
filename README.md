# 🏠 Habito - Moteur de recherche immobilier intelligent

Moteur de recherche d'annonces immobilières utilisant la recherche vectorielle (embeddings) et le reranking pour des résultats pertinents.

## 🏗️ Architecture

### Stack technique
- **Frontend** : Vue 3 + TypeScript + Tailwind CSS
- **Backend** : FastAPI (Python 3.12)
- **Base de données vectorielle** : Qdrant
- **Embeddings** : Ollama (modèle `nomic-embed-text`)
- **Reranking** : Algorithme lexical avec boost sur correspondance ville/mots-clés

### Flow de recherche
```
Query utilisateur
    ↓
🔤 Embedding (Ollama)
    ↓
🔍 Recherche vectorielle (Qdrant)
    ↓
⚡ Reranking lexical
    ↓
📊 Résultats triés
```

## 📋 Prérequis

- Docker & Docker Compose
- Ollama installé localement avec le modèle `nomic-embed-text`
- Python 3.12+ (pour l'ingestion en local)
- Git

## 🚀 Installation

### 1. Cloner le repository
```bash
git clone https://github.com/Najinc/habito.git
cd habito
```

### 2. Installer Ollama et le modèle d'embedding

**Sur Windows :**
```bash
# Télécharger Ollama depuis https://ollama.ai/download
winget install Ollama.Ollama

# Télécharger le modèle d'embedding
ollama pull nomic-embed-text
```

**Sur Linux/Mac :**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull nomic-embed-text
```

### 3. Configurer les variables d'environnement (optionnel)

Créer un fichier `.env` à la racine du projet :
```env
# Qdrant
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=habito_ads

# Ollama
OLLAMA_URL=http://host.docker.internal:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
EMBEDDING_DIM=384

# Search
SEARCH_LIMIT=10
```

### 4. Lancer les services Docker
```bash
docker-compose up -d
```

**Services disponibles :**
- Frontend : http://localhost:3000
- Backend API : http://localhost:8000
- Qdrant Dashboard : http://localhost:6333/dashboard
- Documentation API : http://localhost:8000/docs

## 📊 Ingestion des données

### 🐳 Via Docker (Recommandé)

**Mode simple (1 page par ville) :**
```bash
docker-compose run --rm ingestion
```

**Mode progressif (multi-pages, multi-villes) :**
```bash
docker-compose run --rm \
  -e LBC_PROGRESSIVE=true \
  -e LBC_MAX_PAGES=3 \
  -e LBC_LOCATIONS="Paris:48.8566:2.3522;Lille:50.6292:3.0573;Lyon:45.7640:4.8357" \
  ingestion
```

**Exemple avec configuration complète :**
```bash
docker-compose run --rm \
  -e LBC_TEXT="appartement" \
  -e LBC_PROGRESSIVE=true \
  -e LBC_MAX_PAGES=5 \
  -e LBC_LOCATIONS="Paris:48.8566:2.3522;Lille:50.6292:3.0573;Reims:49.2583:4.0317" \
  -e LBC_PRICE_MIN=600 \
  -e LBC_PRICE_MAX=1200 \
  ingestion
```

**Ou via un fichier .env :**
```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer .env avec vos paramètres
# Puis lancer :
docker-compose --env-file .env run --rm ingestion
```

### 🐍 Via Python local (Alternative)

**Installation des dépendances :**
```bash
cd ingestion
pip install -r requirements.txt
```

**Lancement :**
```bash
# Mode simple
python ingest_lbc.py

# Mode progressif
LBC_PROGRESSIVE=true \
LBC_MAX_PAGES=3 \
LBC_LOCATIONS="Paris:48.8566:2.3522;Lille:50.6292:3.0573" \
python ingest_lbc.py
```

### Variables d'environnement disponibles

| Variable | Défaut | Description |
|----------|--------|-------------|
| `LBC_TEXT` | `appartement` | Texte de recherche |
| `LBC_LOCATIONS` | `Paris:48.8566:2.3522;...` | Villes (format: `Ville:Lat:Lng` séparés par `;`) |
| `LBC_RADIUS` | `10000` | Rayon de recherche en mètres |
| `LBC_PRICE_MIN` | `500` | Prix minimum |
| `LBC_PRICE_MAX` | `1500` | Prix maximum |
| `LBC_PAGE` | `1` | Page de départ |
| `LBC_LIMIT` | `35` | Résultats par page |
| `LBC_PROGRESSIVE` | `false` | Mode progressif (plusieurs pages) |
| `LBC_MAX_PAGES` | `1` | Nombre de pages par ville |
| `EMBEDDING_MODE` | `hash` | Mode d'embedding (`hash` ou `sentence`) |

## 🔍 Utilisation

### Recherche via le frontend
1. Ouvrir http://localhost:3000
2. Entrer une requête (ex: "appartement 2 pièces Paris")
3. Les résultats sont triés par pertinence (score vectoriel + reranking)

### API Backend

**Endpoint de recherche :**
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "appartement 3 pièces Paris proche métro"}'
```

**Documentation interactive :**
- Swagger UI : http://localhost:8000/docs
- ReDoc : http://localhost:8000/redoc

## 🛠️ Développement

### Backend (sans Docker)
```bash
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

### Frontend (sans Docker)
```bash
cd frontend/habito-front
npm install
npm run dev
# Accessible sur http://localhost:5173
```

### Qdrant local
```bash
docker run -p 6333:6333 qdrant/qdrant:v1.13.4
```

## 📁 Structure du projet

```
habito/
├── backend/
│   ├── src/
│   │   ├── main.py                 # Point d'entrée FastAPI
│   │   ├── routes/
│   │   │   └── search.py            # Endpoint de recherche
│   │   ├── services/
│   │   │   ├── ollama.py            # Service d'embedding
│   │   │   ├── qdrant.py            # Client Qdrant
│   │   │   └── rerank.py            # Service de reranking
│   │   └── models/
│   │       ├── search.py            # Modèles de requête
│   │       └── listing.py           # Modèles de réponse
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── habito-front/
│       ├── src/
│       │   ├── App.vue
│       │   └── components/
│       ├── Dockerfile
│       ├── nginx.conf
│       └── package.json
├── ingestion/
│   ├── ingest_lbc.py                # Script d'ingestion Leboncoin
│   └── requirements.txt
├── docker-compose.yml
└── README.md
```

## 🔧 Technologies détaillées

### Backend
- **FastAPI** : Framework web async
- **httpx** : Client HTTP async pour Ollama et Qdrant
- **Qdrant** : Base de données vectorielle (HNSW index, distance cosinus)
- **Ollama** : Modèle d'embedding local `nomic-embed-text` (384 dimensions)

### Reranking
Le service de reranking améliore les résultats de la recherche vectorielle :
- **Boost lexical** : +0.8 si la requête complète est dans le document
- **Boost par token** : +0.4 par mot-clé trouvé
- **Boost ville** : +1.4 si un token correspond à la ville

### Ingestion
- **lbc** : Client Python pour scraper Leboncoin
- Extraction automatique de : surface (m²), nombre de pièces, ville
- Embedding via hash (fallback si Ollama indisponible)
- Mode progressif avec sauvegarde d'état

## 🐛 Troubleshooting

### Ollama n'est pas accessible
```bash
# Vérifier qu'Ollama tourne
ollama list

# Vérifier le modèle
ollama pull nomic-embed-text

# Tester l'embedding
curl http://localhost:11434/api/embed -d '{
  "model": "nomic-embed-text",
  "input": "test"
}'
```

### Erreur "Datadome" lors de l'ingestion
Le scraping Leboncoin peut être bloqué par Datadome (rate limiting).
- Réduire `LBC_MAX_PAGES`
- Attendre quelques minutes entre les exécutions
- Utiliser un VPN ou changer de réseau

### Qdrant collection n'existe pas
La collection est créée automatiquement lors de la première ingestion.
```bash
cd ingestion
python ingest_lbc.py
```

### Le frontend ne communique pas avec le backend
Vérifier que les services Docker sont bien lancés :
```bash
docker-compose ps
docker-compose logs backend
```

## 📝 TODO / Améliorations futures

- [ ] Ajouter filtres avancés (prix, surface, ville)
- [ ] Implémenter le reranking avec un modèle de cross-encoding
- [ ] Support d'autres sources d'annonces (SeLoger, PAP)
- [ ] Cache Redis pour les embeddings fréquents
- [ ] Interface admin pour gérer les ingestions
- [ ] Tests unitaires et d'intégration
- [ ] CI/CD avec GitHub Actions

---

**Auteur** : Najib CHAFEI
**License** : MIT
