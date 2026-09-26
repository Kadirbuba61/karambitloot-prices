#!/usr/bin/env python3
"""
KarambitLoot — Steam CS2 Fiyat Çekici (v6.0)
ByMykel yeni format: { "metadata": {...}, "prices": { "skin": cents, ... } }
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

SOURCES = [
    {
        "name": "ByMykel (yeni format)",
        "url": "https://raw.githubusercontent.com/ByMykel/counter-strike-price-tracker/main/static/latest.json",
        "headers": {"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    },
    {
        "name": "CSGOTrader",
        "url": "https://prices.csgotrader.app/latest/prices_v6.json",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://csgotrader.app/",
        }
    },
]

OUTPUT_FILE = "prices.json"
DISCOUNT = 0.95
MIN_PRICE = 0.03
TIMEOUT = 180


def fetch_json(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        text = response.read().decode("utf-8", errors="replace")
        if text.lstrip().startswith("<"):
            raise ValueError("JSON yerine HTML döndü (Cloudflare)")
        return json.loads(text)


def extract_price(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if value > 0 else None
    if isinstance(value, dict):
        steam = value.get("steam")
        if isinstance(steam, dict):
            for k in ("last_24h", "last_7d", "last_30d", "price", "last"):
                v = steam.get(k)
                if isinstance(v, (int, float)) and v > 0:
                    return float(v)
        if isinstance(steam, (int, float)) and steam > 0:
            return float(steam)
        for k in ("price", "last_24h", "lowest_price", "lowest", "median_price"):
            v = value.get(k)
            if isinstance(v, (int, float)) and v > 0:
                return float(v)
    return None


def main():
    print("=" * 60)
    print("📡 KarambitLoot Price Fetcher v6.0")
    print("=" * 60)

    raw = None
    used_source = None
    for src in SOURCES:
        print(f"\n⬇️  Deneniyor: {src['name']}")
        try:
            raw = fetch_json(src["url"], src["headers"])
            used_source = src["name"]
            print(f"   ✅ Başarılı! {len(raw)} üst-seviye key.")
            break
        except Exception as e:
            print(f"   ❌ {type(e).__name__}: {e}")

    if raw is None:
        print("\n❌ Hiçbir kaynak çalışmadı.")
        return 1

    if not isinstance(raw, dict):
        print(f"❌ Beklenmeyen format: {type(raw).__name__}")
        return 1

    # ⭐ KRİTİK: ByMykel yeni format içinde "prices" key'i var mı?
    price_list = raw
    price_divisor = 1.0
    if "prices" in raw and isinstance(raw["prices"], dict):
        print(f"\n🔍 'prices' içinde bulundu, asıl fiyatlar orada!")
        price_list = raw["prices"]
        # Metadata'da currency USD ve cent cinsinden mi kontrol et
        meta = raw.get("metadata", {})
        print(f"   Metadata: {json.dumps(meta)[:150]}")
        # ByMykel fiyatları cent cinsinden → 100'e böl
        price_divisor = 100.0
        print(f"   Fiyatlar cent cinsinden → ÷100 uygulanacak")

    print(f"\n📋 Örnek 3 item (ham):")
    for i, (k, v) in enumerate(list(price_list.items())[:3]):
        print(f"   {i+1}. {k} → {v}")

    # İşle
    prices = {}
    skipped = 0
    for name, value in price_list.items():
        if not name or not isinstance(name, str):
            skipped += 1
            continue
        # Internal/atılacak isimler
        if name.startswith(("#", "Sticker", "Patch", "Graffiti", "Music Kit", "Agent", "Collectible", "Key", "Pass", "Tool", "Tag", "Container", "metadata")):
            skipped += 1
            continue
        price = extract_price(value)
        if price is None:
            skipped += 1
            continue
        # Cent → dolar
        price = price / price_divisor
        if price < MIN_PRICE:
            skipped += 1
            continue
        prices[name] = round(price * DISCOUNT, 2)

    print(f"\n✅ {len(prices)} fiyat işlendi (%{(1-DISCOUNT)*100:.0f} indirimli)")
    print(f"⏭️  {skipped} item atlandı")

    if len(prices) < 100:
        print(f"\n📋 İlk 5 fiyat örneği (sonuç):")
        for k, v in list(prices.items())[:5]:
            print(f"   {k} → ${v}")
        print(f"⚠️  Az veri ama yazılıyor...")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(prices, f, ensure_ascii=False, indent=2, sort_keys=True)

    print(f"\n✅ {len(prices)} fiyat {OUTPUT_FILE}'a yazıldı")
    return 0


if __name__ == "__main__":
    sys.exit(main())
