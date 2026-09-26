#!/usr/bin/env python3
"""
CS:GO/CS2 skin fiyatlarını CSGOBackpack API'den çeker.
Tek istekte tüm fiyatlar gelir.
"""

import json
import urllib.request
from pathlib import Path

OUTPUT_FILE = "prices.json"
DISCOUNT = 0.95  # %5 indirim

# CSGOBackpack API - tüm item listesi (tek istek)
API_URL = "https://csgobackpack.net/api/GetItemsList/v2/"


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
    print("📥 CSGOBackpack API'den tüm fiyatlar çekiliyor...")

    try:
        data = fetch_url(API_URL)
        parsed = json.loads(data)
    except Exception as e:
        print(f"❌ API hatası: {e}")
        return

    if not parsed.get("success"):
        print("❌ API başarısız döndü")
        return

    items = parsed.get("items", {})
    print(f"📦 Toplam {len(items)} item alındı")

    prices = {}
    skipped = 0

    for name, info in items.items():
        try:
            # price_24h daha güncel, yoksa price kullan
            price_data = info.get("price") or {}
            usd_str = price_data.get("24h") or price_data.get("all_time") or price_data.get("7d")

            if not usd_str:
                skipped += 1
                continue

            usd_price = float(usd_str)
            if usd_price <= 0:
                skipped += 1
                continue

            # %5 indirim uygula
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
