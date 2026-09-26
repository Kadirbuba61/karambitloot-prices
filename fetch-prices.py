#!/usr/bin/env python3
"""
Steam CS2 fiyatlarını ByMykel'in price tracker reposundan çeker.
Bu repo her gün güncelleniyor ve Steam fiyatlarını içeriyor.
"""

import json
import urllib.request
from pathlib import Path

OUTPUT_FILE = "prices.json"
DISCOUNT = 0.95  # %5 indirim

# ByMykel'in counter-strike-price-tracker reposu
# Her gün güncellenen Steam fiyatları
API_URL = "https://raw.githubusercontent.com/ByMykel/counter-strike-price-tracker/main/static/prices/latest.json"


def fetch_url(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=60) as response:
                return response.read()
        except Exception as e:
            if attempt < retries - 1:
                import time
                time.sleep(3)
            else:
                raise e


def main():
    print("📥 ByMykel Price Tracker'dan fiyatlar çekiliyor...")
    print(f"   URL: {API_URL}")

    try:
        data = fetch_url(API_URL)
        parsed = json.loads(data)
    except Exception as e:
        print(f"❌ API hatası: {e}")
        return

    # Format: [{"name": "...", "price": 12.34, ...}, ...]
    if not isinstance(parsed, list):
        print(f"❌ Beklenmedik format: {type(parsed)}")
        return

    print(f"📦 Toplam {len(parsed)} item alındı")

    prices = {}
    skipped = 0

    for item in parsed:
        try:
            name = item.get("name") or item.get("market_hash_name")
            if not name:
                skipped += 1
                continue

            # price veya steam_price_median
            usd_price = item.get("price") or item.get("steam") or item.get("steam_price")

            if usd_price is None:
                skipped += 1
                continue

            usd_price = float(usd_price)
            if usd_price <= 0:
                skipped += 1
                continue

            # %5 indirim
            discounted = round(usd_price * DISCOUNT, 2)
            prices[name] = discounted

        except (ValueError, TypeError, KeyError):
            skipped += 1
            continue

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Tamamlandı!")
    print(f"   Toplam çekilen: {len(prices)}")
    print(f"   Atlanan: {skipped}")
    print(f"   Kaydedildi: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
