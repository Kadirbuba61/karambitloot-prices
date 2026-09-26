#!/usr/bin/env python3
"""
KarambitLoot — Steam CS2 Fiyat Çekici (v2.0)

ByMykel'in counter-strike-price-tracker reposundan hazır Steam fiyatlarını çeker.
Tek istek, ~10 saniyede biter. GitHub Actions timeout riski yok.

Çıktı formatı: { "skin_name": fiyat, ... }  (%5 indirimli)
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# YAPILANDIRMA
# ═══════════════════════════════════════════════════════════
PRICE_TRACKER_URL = "https://raw.githubusercontent.com/ByMykel/counter-strike-price-tracker/main/static/prices/latest.json"
OUTPUT_FILE = "prices.json"
DISCOUNT = 0.95              # %5 indirim (0.95 = %5 az)
MIN_PRICE = 0.03             # Çok düşük fiyatları atla (0.03$ altı)
TIMEOUT = 60                 # İstek timeout (saniye)
USER_AGENT = "KarambitLoot-PriceFetcher/2.0 (https://github.com/Kadirbuba61)"


def fetch_json(url: str) -> dict:
    """URL'den JSON çeker."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        data = response.read()
        return json.loads(data)


def extract_price(value):
    """
    ByMykel fiyat tracker farklı formatlar dönebilir, hepsini destekle:
      - number: 25.50
      - dict:   { "steam": { "last_24h": 25.50 }, ... }
      - dict:   { "steam": 25.50 }
      - dict:   { "price": 25.50 }
    """
    if value is None:
        return None

    # Direkt sayı
    if isinstance(value, (int, float)):
        return float(value)

    # Dict formatları
    if isinstance(value, dict):
        # Öncelik: steam → price → lowest → diğer
        for key in ("steam", "price", "lowest_price", "lowest"):
            if key in value:
                v = value[key]
                if isinstance(v, (int, float)):
                    return float(v)
                if isinstance(v, dict):
                    # Örn: { "last_24h": 25.5, "last_7d": ... }
                    for sub in ("last_24h", "last_7d", "last_30d", "value", "price"):
                        if sub in v and isinstance(v[sub], (int, float)):
                            return float(v[sub])
                    # Herhangi bir numeric alan
                    for sub_v in v.values():
                        if isinstance(sub_v, (int, float)) and sub_v > 0:
                            return float(sub_v)

        # Hiçbiri yoksa: ilk numeric value'yu al
        for v in value.values():
            if isinstance(v, (int, float)) and v > 0:
                return float(v)

    return None


def main() -> int:
    print("=" * 60)
    print("📡 KarambitLoot Price Fetcher v2.0")
    print("=" * 60)
    print(f"Kaynak: {PRICE_TRACKER_URL}")
    print(f"İndirim: %{(1 - DISCOUNT) * 100:.0f}")
    print(f"Çıktı: {OUTPUT_FILE}")
    print()

    # Mevcut fiyatları yükle (fallback — kaynak çökerse eski veri kalsın)
    existing = {}
    if Path(OUTPUT_FILE).exists():
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
            print(f"📦 Mevcut {len(existing)} fiyat yedek olarak yüklendi.")
        except Exception as e:
            print(f"⚠️  Mevcut {OUTPUT_FILE} okunamadı: {e}")

    # Kaynaktan çek
    try:
        print("⬇️  Fiyatlar çekiliyor...")
        raw = fetch_json(PRICE_TRACKER_URL)
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP hatası: {e.code} {e.reason}")
        return 1
    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")
        return 1

    if not isinstance(raw, dict):
        print(f"❌ Beklenmeyen format: {type(raw).__name__}")
        return 1

    print(f"✅ Kaynaktan {len(raw)} item alındı.")
    print()

    # İşle
    prices = {}
    skipped = 0
    for name, value in raw.items():
        if not name or not isinstance(name, str):
            skipped += 1
            continue
        price = extract_price(value)
        if price is None or price < MIN_PRICE:
            skipped += 1
            continue
        # %5 indirim + 2 ondalık
        discounted = round(price * DISCOUNT, 2)
        prices[name] = discounted

    print(f"✅ {len(prices)} fiyat işlendi (%{(1 - DISCOUNT) * 100:.0f} indirimli)")
    print(f"⏭️  {skipped} item atlandı (fiyat yok / çok düşük)")

    # Kaynak çöktüyse veya boş dönerse: eski veriyi koru
    if len(prices) < 100 and existing:
        print(f"⚠️  Yeni veri az ({len(prices)} item). Mevcut {len(existing)} fiyat korunuyor.")
        # Sadece yeni gelenleri güncelle, eskileri koru
        existing.update(prices)
        prices = existing
        print(f"📦 Toplam: {len(prices)} fiyat (eski + yeni)")

    # Kaydet
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(prices, f, ensure_ascii=False, indent=2, sort_keys=True)
        print()
        print("=" * 60)
        print(f"✅ BAŞARILI — {len(prices)} fiyat {OUTPUT_FILE}'a yazıldı.")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"❌ Dosya yazma hatası: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
