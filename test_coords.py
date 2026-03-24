#!/usr/bin/env python3
import httpx
import time
import json

print("🔄 Forçage de l'ingestion...")
# Force ingest
response = httpx.post(
    'http://localhost:8000/api/ingest',
    json={
        'search_text': 'appartement',
        'city': 'Lille',
        'lat': 50.6292,
        'lng': 3.0573,
        'radius': 10000
    },
    timeout=30
)

print(f"Ingest status: {response.status_code}")
print(f"Response: {response.json()}")

print("\n⏳ Attente 5 secondes pour ingestion complète...")
time.sleep(5)

print("\n🔍 Vérification des données...")
search_response = httpx.post(
    'http://localhost:8000/api/search',
    json={'query': 'appartement', 'city': 'Lille'},
    timeout=30
)

if search_response.status_code == 200:
    data = search_response.json()
    print(f"✓ {len(data)} résultats")
    if data:
        first = data[0]['payload']
        print(f"\nPremière annonce:")
        print(f"  Titre: {first.get('subject', 'N/A')}")
        print(f"  Lat: {first.get('lat')}")
        print(f"  Lng: {first.get('lng')}")
        
        # Check all results
        with_coords = sum(1 for r in data if r['payload'].get('lat') and r['payload'].get('lng'))
        print(f"\n📍 {with_coords}/{len(data)} annonces ont des coordonnées GPS")
        
        if with_coords > 0:
            print("\n✅ Excellente! Les coordonnées GPS sont maintenant présentes!")
        else:
            print("\n⚠️  Les coordonnées GPS sont toujours absentes")
else:
    print(f"✗ Erreur: {search_response.status_code}")
    print(search_response.text)
