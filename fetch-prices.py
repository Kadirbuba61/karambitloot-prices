#!/usr/bin/env python3
"""
KarambitLoot — Steam CS2 Fiyat Çekici (v4.0)
Kaynak: prices.csgotrader.app (gerçek Steam Market fiyatları)
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

# ═══════════════════════════════════════════════════════════
SOURCES = [
    "https://prices.csgotrader.app/latest/prices_v6.json",
    "https://raw.githubusercontent.com/ByMykel/counter-strike-price-tracker/main/static/prices/latest.json",
]
OUTPUT_FILE = "prices.json"
DISCOUNT = 0.95
MIN_PRICE = 0.03
TIMEOUT = 180
USER_AGENT = "KarambitLoot-PriceFetcher/4.0"


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return json.loads(response.read())


def extract_price(value):
    """Farklı formatları dene: sayı, {steam:{last_24h:..}}, {price:..} vb."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if value > 0 else None
    if isinstance(value, dict):
        # steam alt yapısı
        steam = value.get("steam")
        if isinstance(steam, dict):
            for k in ("last_24h", "last_7d", "last_30d", "price"):
                v = steam.get(k)
                if isinstance(v, (int, float)) and v > 0:
                    return float(v)
        if isinstance(steam, (int, float)) and steam > 0:
            return float(steam)
        # direkt alanlar
        for k in ("price", "last_24h", "lowest_price", "lowest", "median_price"):
            v = value.get(k)
            if isinstance(v, (int, float)) and v > 0:
                return float(v)
    return None


def main():
    print("=" * 60)
    print("📡 KarambitLoot Price Fetcher v4.0")
    print("=" * 60)

    raw = None
    used_source = None
    for url in SOURCES:
        print(f"⬇️  Deneniyor: {url}")
        try:
            raw = fetch_json(url)
            used_source = url
            print(f"✅ Başarılı! {len(raw)} item alındı.")
            break
        except urllib.error.HTTPError as e:
            print(f"   ❌ HTTP {e.code}: {e.reason}")
        except Exception as e:
            print(f"   ❌ Hata: {type(e).__name__}: {e}")

    if raw is None:
        print("❌ Hiçbir kaynak çalışmadı.")
        return 1

    if not isinstance(raw, dict):
        print(f"❌ Beklenmeyen format: {type(raw).__name__} (dict bekleniyordu)")
        return 1

    # İlk 3 örneği logla (format kontrolü için)
    print("\n📋 Format örneği (ilk 3 item):")
    for i, (k, v) in enumerate(list(raw.items())[:3]):
        print(f"   {i+1}. {k}")
        print(f"      {json.dumps(v)[:200]}")

    # İşle
    prices = {}
    skipped = 0
    for name, value in raw.items():
        if not name or not isinstance(name, str):
            skipped += 1
            continue
        # Gereksiz item'ları atla
        if name.startswith(("Sticker", "Patch", "Graffiti", "Music Kit", "Agent", "Collectible", "Key", "Pass", "Tool", "Tag", "Container")):
            skipped += 1
            continue
        price = extract_price(value)
        if price is None or price < MIN_PRICE:
            skipped += 1
            continue
        prices[name] = round(price * DISCOUNT, 2)

    print(f"\n✅ {len(prices)} fiyat işlendi")
    print(f"⏭️  {skipped} item atlandı")

    if len(prices) < 100:
        print(f"⚠️  Çok az veri ({len(prices)}). Yine de kaydediliyor.")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(prices, f, ensure_ascii=False, indent=2, sort_keys=True)

    print(f"\n✅ {len(prices)} fiyat {OUTPUT_FILE}'a yazıldı")
    return 0


if __name__ == "__main__":
    sys.exit(main())
