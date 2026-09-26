#!/usr/bin/env python3
"""
CS:GO/CS2 skin fiyatlarını Skinport API'den çeker.
Tek istekte tüm fiyatlar gelir.
"""

import json
import gzip
import urllib.request
from pathlib import Path

OUTPUT_FILE = "prices.json"
DISCOUNT = 0.95  # %5 indirim

# Skinport API - tüm item listesi (tek istek, ücretsiz)
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=USD"


def fetch_url(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Encoding': 'gzip'
            })
            with urllib.request.urlopen(req, timeout=60) as response:
                data = response.read()
                # gzip decompress (Skinport gzip ile döner)
                if response.headers.get('Content-Encoding') == 'gzip':
                    data = gzip.decompress(data)
                return data
        except Exception as e:
            if attempt < retries - 1:
                import time
                time.sleep(3)
            else:
                raise e


def main():
    print("📥 Skinport API'den tüm fiyatlar çekiliyor...")

    try:
        data = fetch_url(API_URL)
        items = json.loads(data)
    except Exception as e:
        print(f"❌ API hatası: {e}")
        return

    print(f"📦 Toplam {len(items)} item alındı")

    prices = {}
    skipped = 0

    for item in items:
        try:
            name = item.get("market_hash_name")
            if not name:
                skipped += 1
                continue

            # min_price (en ucuz satıcı) öncelikli, yoksa suggested_price
            usd_price = item.get("min_price") or item.get("suggested_price")

            if not usd_price:
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

    # Kaydet
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Tamamlandı!")
    print(f"   Toplam çekilen: {len(prices)}")
    print(f"   Atlanan: {skipped}")
    print(f"   Kaydedildi: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
