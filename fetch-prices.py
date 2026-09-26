#!/usr/bin/env python3
"""
KarambitLoot — Steam CS2 Fiyat Çekici (v3.0)

ByMykel CSGO-API'nin skins.json'undaki 'price' alanını kullanır.
%5 indirim uygular ve prices.json'a yazar.

Not: CSGO-API'nin kendisi zaten Steam fiyatlarını içeriyor,
bu yüzden ekstra bir tracker reposuna ihtiyaç yok.
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# YAPILANDIRMA
# ═══════════════════════════════════════════════════════════
CSGO_API_URL = "https://raw.githubusercontent.com/ByMykel/CSGO-API/main/public/api/en/skins.json"
OUTPUT_FILE = "prices.json"
DISCOUNT = 0.95              # %5 indirim (0.95 = %5 az)
MIN_PRICE = 0.03             # Çok düşük fiyatları atla
TIMEOUT = 120                # Büyük dosya, 2 dk timeout
USER_AGENT = "KarambitLoot-PriceFetcher/3.0 (https://github.com/Kadirbuba61)"


def fetch_json(url: str):
    """URL'den JSON çeker."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return json.loads(response.read())


def main() -> int:
    print("=" * 60)
    print("📡 KarambitLoot Price Fetcher v3.0 (CSGO-API)")
    print("=" * 60)
    print(f"Kaynak: {CSGO_API_URL}")
    print(f"İndirim: %{(1 - DISCOUNT) * 100:.0f}")
    print(f"Çıktı: {OUTPUT_FILE}")
    print()

    # Mevcut fiyatları yedek olarak yükle
    existing = {}
    if Path(OUTPUT_FILE).exists():
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
            print(f"📦 Mevcut {len(existing)} fiyat yedek olarak yüklendi.")
        except Exception as e:
            print(f"⚠️  Mevcut {OUTPUT_FILE} okunamadı: {e}")

    # CSGO-API'den çek
    try:
        print("⬇️  CSGO-API'den skinler çekiliyor (30-60 sn sürebilir)...")
        skins = fetch_json(CSGO_API_URL)
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP hatası: {e.code} {e.reason}")
        return 1
    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")
        return 1

    if not isinstance(skins, list):
        print(f"❌ Beklenmeyen format: {type(skins).__name__}")
        return 1

    print(f"✅ {len(skins)} skin alındı.")
    print()

    # İşle
    prices = {}
    skipped = 0
    for skin in skins:
        if not isinstance(skin, dict):
            skipped += 1
            continue
        name = skin.get("name")
        price = skin.get("price")
        if not name or not isinstance(price, (int, float)) or price < MIN_PRICE:
            skipped += 1
            continue
        # %5 indirim + 2 ondalık
        prices[name] = round(price * DISCOUNT, 2)

    print(f"✅ {len(prices)} fiyat işlendi (%{(1 - DISCOUNT) * 100:.0f} indirimli)")
    print(f"⏭️  {skipped} item atlandı (fiyat yok / çok düşük)")

    # Kaynak çöktüyse: eski veriyi koru
    if len(prices) < 100 and existing:
        print(f"⚠️  Yeni veri az ({len(prices)}). Mevcut {len(existing)} fiyat korunuyor.")
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
