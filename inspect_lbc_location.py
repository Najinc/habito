#!/usr/bin/env python3
import lbc

# Inspect LBC Ad structure
client = lbc.Client()
result = client.search(
    text='appartement',
    locations=[lbc.City(lat=50.6292, lng=3.0573, radius=10000, city='Lille')],
    limit=1,
    ad_type=lbc.AdType.OFFER,
    category=lbc.Category.IMMOBILIER,
)

if result.ads:
    ad = result.ads[0]
    print("🔍 Full Ad object:")
    print(f"  Has lat: {hasattr(ad, 'lat')}")
    print(f"  Has lng: {hasattr(ad, 'lng')}")
    print(f"  Has location: {hasattr(ad, 'location')}")
    
    if hasattr(ad, 'location'):
        loc = ad.location
        print(f"\n📍 Location object: {type(loc)}")
        print(f"   Location repr: {loc}")
        
        if loc:
            print(f"\n   Attributes of Location:")
            for attr in dir(loc):
                if not attr.startswith('_'):
                    try:
                        value = getattr(loc, attr)
                        if not callable(value):
                            print(f"     {attr} = {value}")
                    except:
                        pass
else:
    print("No ads found")
