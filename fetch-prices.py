#!/usr/bin/env python3
"""
ByMykel'in counter-strike-price-tracker reposundan
hazır Steam fiyatlarını çeker, %5 indirim uygular.
Tek istek, 5 saniyede biter.
"""

import json
import urllib.request
from pathlib import Path

# ByMykel'in hazır fiyat tracker'ı (günlük güncelleniyor)
PRICE_TRACKER_URL = "https://raw.githubusercontent.com/ByMykel/counter-strike-price-tracker/main/static/prices/latest.json"
OUTPUT_FILE = "prices.json"
DISCOUNT = 0.95  # %5 indirim

def fetch_json(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 KarambitLoot-PriceFetcher/1.0'
    })
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read())

def main():
    print("📡 ByMykel price tracker'dan fiyatlar çekiliyor...")
    try:
        data = fetch_json(PRICE_TRACKER_URL)
    except Exception as e:
        print(f"❌ Hata: {e}")
        return 1

    # ByMykel formatı: { "AK-47 | Redline (Field-Tested)": { "price": 25.50, ... }, ... }
    # veya direkt: { "AK-47 | Redline (Field-Tested)": 25.50 }
    prices = {}
    count = 0

    for name, val in data.items():
        price = None
        if isinstance(val, dict):
            price = val.get('price') or val.get('steam') or val.get('lowest_price')
        elif isinstance(val, (int, float)):
            price = val

        if price and price > 0:
            prices[name] = round(price * DISCOUNT, 2)
            count += 1

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)

    print(f"✅ {count} skin fiyatı kaydedildi → {OUTPUT_FILE}")
    return 0

if __name__ == "__main__":
    exit(main())
