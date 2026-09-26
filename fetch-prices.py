#!/usr/bin/env python3
"""
KarambitLoot — Steam CS2 Fiyat Çekici (v5.0)
Kaynak: prices.csgotrader.app (Cloudflare bypass + ByMykel yeni URL fallback)
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# KAYNAKLAR (sırayla denenir)
# ═══════════════════════════════════════════════════════════
SOURCES = [
    {
        "name": "CSGOTrader",
        "url": "https://prices.csgotrader.app/latest/prices_v6.json",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://csgotrader.app/",
            "Origin": "https://csgotrader.app",
        }
    },
    {
        "name": "ByMykel (yeni URL)",
        "url": "https://raw.githubusercontent.com/ByMykel/counter-strike-price-tracker/main/static/latest.json",
        "headers": {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }
    },
]

OUTPUT_FILE = "prices.json"
DISCOUNT = 0.95
MIN_PRICE = 0.03
TIMEOUT = 180


def fetch_json(url, headers, timeout=TIMEOUT):
    """URL'den JSON çeker, Cloudflare'e yakalanmamak için tam header seti gönderir."""
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
        # Bazen Cloudflare HTML döndürür, kontrol et
        text = raw.decode("utf-8", errors="replace")
        if text.lstrip().startswith("<"):
            raise ValueError("Sunucu JSON yerine HTML döndürdü (Cloudflare koruması olabilir)")
        return json.loads(text)


def extract_price(value):
    """Farklı formatları dene: sayı, {steam:{last_24h:..}}, {price:..} vb."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if value > 0 else None
    if isinstance(value, dict):
        # steam alt yapısı (CSGOTrader formatı)
        steam = value.get("steam")
        if isinstance(steam, dict):
            for k in ("last_24h", "last_7d", "last_30d", "price", "last"):
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
    print("📡 KarambitLoot Price Fetcher v5.0")
    print("=" * 60)

    raw = None
    used_source = None
    for src in SOURCES:
        print(f"\n⬇️  Deneniyor: {src['name']}")
        print(f"   URL: {src['url']}")
        try:
            raw = fetch_json(src["url"], src["headers"])
            used_source = src["name"]
            print(f"   ✅ Başarılı! {len(raw)} item alındı.")
            break
        except urllib.error.HTTPError as e:
            print(f"   ❌ HTTP {e.code}: {e.reason}")
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON parse hatası: {e}")
        except ValueError as e:
            print(f"   ❌ {e}")
        except Exception as e:
            print(f"   ❌ Hata: {type(e).__name__}: {e}")

    if raw is None:
        print("\n❌ Hiçbir kaynak çalışmadı.")
        return 1

    if not isinstance(raw, dict):
        print(f"❌ Beklenmeyen format: {type(raw).__name__} (dict bekleniyordu)")
        return 1

    # İlk 3 örneği logla
    print(f"\n📋 Format örneği (ilk 3 item):")
    for i, (k, v) in enumerate(list(raw.items())[:3]):
        print(f"   {i+1}. {k}")
        preview = json.dumps(v)[:200] if not isinstance(v, (int, float)) else str(v)
        print(f"      {preview}")

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

    print(f"\n✅ {len(prices)} fiyat işlendi (%{(1-DISCOUNT)*100:.0f} indirimli)")
    print(f"⏭️  {skipped} item atlandı")

    if len(prices) < 100:
        print(f"⚠️  Çok az veri ({len(prices)}). Kaynak bozuk olabilir.")
        return 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(prices, f, ensure_ascii=False, indent=2, sort_keys=True)

    print(f"\n✅ {len(prices)} fiyat {OUTPUT_FILE}'a yazıldı")
    return 0


if __name__ == "__main__":
    sys.exit(main())
