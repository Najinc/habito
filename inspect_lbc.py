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
    print("Attributes of LBC Ad object:")
    print("=" * 60)
    for attr in sorted(dir(ad)):
        if not attr.startswith('_'):
            try:
                value = getattr(ad, attr)
                if not callable(value):
                    value_str = str(value)[:150]
                    print(f"{attr:20} = {value_str}")
            except:
                pass
else:
    print("No ads found")
