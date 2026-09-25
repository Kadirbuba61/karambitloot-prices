#!/usr/bin/env python3
"""
Steam Market'ten tüm CS2 skin fiyatlarını çeker.
Fiyatların %5 düşüğünü prices.json dosyasına yazar.
"""

import json
import time
import sys
import urllib.request
import urllib.parse
from pathlib import Path

# ============ YAPILANDIRMA ============
SKINS_JSON_URL = "https://raw.githubusercontent.com/ByMykel/CSGO-API/main/public/api/en/skins.json"
OUTPUT_FILE = "prices.json"
DISCOUNT = 0.95  # %5 indirim (0.95 = %5 az)
REQUEST_DELAY = 1.2  # saniye (Steam rate limit için)
MAX_RETRIES = 3
CURRENCY = 1  # 1 = USD

def fetch_url(url, retries=MAX_RETRIES):
    """URL'den veri çeker, hata durumunda yeniden dener."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.read()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise e

def fetch_steam_price(market_hash_name):
    """Steam Market'ten tek bir item'ın fiyatını çeker."""
    encoded_name = urllib.parse.quote(market_hash_name)
    url = f"https://steamcommunity.com/market/priceoverview/?appid=730&currency={CURRENCY}&market_hash_name={encoded_name}"
    
    try:
        data = fetch_url(url)
        result = json.loads(data)
        if result.get('success'):
            price_str = result.get('lowest_price', '0')
            # "$25.50" → 25.50
            price_str = price_str.replace('$', '').replace(',', '').replace('€', '').replace('₺', '').strip()
            price = float(price_str)
            return price
    except Exception:
        pass
    return None

def load_skins():
    """CSGO-API'den tüm skinleri yükler."""
    print("CSGO-API'den skin listesi yükleniyor...")
    data = fetch_url(SKINS_JSON_URL)
    skins = json.loads(data)
    print(f"Toplam {len(skins)} skin bulundu.")
    return skins

def main():
    # Mevcut fiyatları yükle (varsa)
    existing_prices = {}
    if Path(OUTPUT_FILE).exists():
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                existing_prices = json.load(f)
            print(f"Mevcut {len(existing_prices)} fiyat yüklendi.")
        except Exception:
            existing_prices = {}
    
    # Skinleri yükle
    skins = load_skins()
    
    # Fiyatları çek
    prices = dict(existing_prices)
    processed = 0
    updated = 0
    failed = 0
    
    for skin in skins:
        market_hash_name = skin.get('name', '')
        if not market_hash_name:
            continue
        
        processed += 1
        price = fetch_steam_price(market_hash_name)
        
        if price and price > 0:
            discounted = round(price * DISCOUNT, 2)
            prices[market_hash_name] = discounted
            updated += 1
            if updated % 25 == 0:
                print(f"  {updated} güncellendi... (son: {market_hash_name} -> ${discounted})")
        else:
            failed += 1
        
        # Rate limit
        time.sleep(REQUEST_DELAY)
    
    # Kaydet
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Tamamlandı!")
    print(f"   İşlenen: {processed}")
    print(f"   Başarılı: {updated}")
    print(f"   Başarısız: {failed}")
    print(f"   Toplam fiyat: {len(prices)}")
    print(f"   Kaydedildi: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()