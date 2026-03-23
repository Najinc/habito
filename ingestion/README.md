# Ingestion Leboncoin avec `lbc`

## Installation

```bash
pip install -r requirements.txt
```

## Lancement

```bash
python ingest_lbc.py
```

## Variables d'environnement utiles

- `QDRANT_HOST` (défaut: `localhost`)
- `QDRANT_PORT` (défaut: `6333`)
- `LBC_TEXT` (défaut: `appartement`)
- `LBC_CITY` (défaut: `Paris`)
- `LBC_LAT` (défaut: `48.8566`)
- `LBC_LNG` (défaut: `2.3522`)
- `LBC_RADIUS` (défaut: `10000`)
- `LBC_LOCATIONS` (défaut: `Paris:48.8566:2.3522;Lille:50.6292:3.0573;Reims:49.2583:4.0317`)
- `LBC_PAGE` (défaut: `1`)
- `LBC_LIMIT` (défaut: `35`)
- `LBC_PRICE_MIN` (défaut: `500`)
- `LBC_PRICE_MAX` (défaut: `1500`)
- `EMBEDDING_MODE` (défaut: `hash`, valeurs: `hash` ou `sentence`)
- `EMBEDDING_DIM` (défaut: `384`)
- `LBC_PROGRESSIVE` (défaut: `false`)
- `LBC_MAX_PAGES` (défaut: `1`, nombre de pages par ville et par exécution)
- `LBC_STATE_FILE` (défaut: `./.ingest_state.json`)

Exemple:

```bash
LBC_CITY=Lille LBC_LAT=50.6292 LBC_LNG=3.0573 LBC_PRICE_MIN=600 LBC_PRICE_MAX=1800 python ingest_lbc.py
```

Pour activer de vrais embeddings (plus lourd, installe `sentence-transformers` + `torch`):

```bash
EMBEDDING_MODE=sentence python ingest_lbc.py
```

Scraping progressif (pagination incrémentale avec reprise):

```bash
LBC_PROGRESSIVE=true LBC_MAX_PAGES=2 python ingest_lbc.py
```

À chaque run, le script reprend à la page suivante par ville (via `LBC_STATE_FILE`) et revient à la page 1 quand il atteint la fin.

## Notes

- Le script utilise la librairie `lbc` (https://github.com/etienne-hd/lbc).
- En cas de `403`, diminuer la fréquence des requêtes ou utiliser un proxy propre (cf. README `lbc`).

## Score dans l'API de recherche

Le score retourné par `POST /api/search` est un score composite:
- base vectorielle de Qdrant (similarité cosine entre la requête et l'annonce)
- bonus lexical appliqué au rerank backend (tokens de la requête présents dans titre/description/doc, et bonus plus fort sur la ville)

Ce score est donc relatif au lot de résultats courant (plus haut = plus pertinent), pas une probabilité absolue.
