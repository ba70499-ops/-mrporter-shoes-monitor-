# MR PORTER メンズシューズ値下げ監視 - エラー時通知なし版

import os
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import sys
import re

CHANNEL_TOKEN = os.getenv('CHANNEL_TOKEN')
MRPORTER_URL = "https://www.mrporter.com/en-us/mens/shoes"
PRICE_DB_FILE = "/tmp/mrporter_prices.json"
LINE_API_URL = "https://api.line.me/v2/bot/message/broadcast"

if not CHANNEL_TOKEN:
    print("❌ CHANNEL_TOKEN 未設定")
    sys.exit(1)

def send_line(text):
    headers = {"Authorization": f"Bearer {CHANNEL_TOKEN}", "Content-Type": "application/json"}
    data = {"messages": [{"type": "text", "text": text}]}
    try:
        r = requests.post(LINE_API_URL, headers=headers, json=data, timeout=10)
        print(f"✅ LINE: {r.status_code}")
        return True
    except:
        return False

def load_db():
    try:
        if os.path.exists(PRICE_DB_FILE):
            with open(PRICE_DB_FILE, 'r') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_db(db):
    with open(PRICE_DB_FILE, 'w') as f:
        json.dump(db, f)

def scrape_mrporter():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        r = requests.get(MRPORTER_URL, headers=headers, timeout=15)
        soup = BeautifulSoup(r.content, 'html.parser')
        products = {}
        
        items = soup.find_all('div', class_=['product-tile', 'product', 'item'])
        for item in items[:30]:
            name = item.find(['h3', 'h2', 'a']).get_text(strip=True)[:50] if item.find(['h3', 'h2', 'a']) else ''
            price_match = re.search(r'\$([\d,]+\.?\d*)', item.get_text())
            if price_match and name:
                price = int(float(price_match.group(1).replace(',', '')) * 100)
                products[name] = price
        
        print(f"👞 MR PORTER: {len(products)}件")
        return products
    except:
        print("❌ MR PORTER スクレイピングエラー（通知なし）")
        return None

def main():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S JST')
    db = load_db()
    
    products = scrape_mrporter()
    if products is None:
        print("📊 エラー → 通知なし（正常）")
        return
    
    drops = []
    for name, price in products.items():
        if name in db and db[name] > price:
            drop_amount = (db[name] - price) / 100
            drops.append(f"👞 {name[:35]} ${db[name]/100:.0f}→${price/100:.0f}")
    
    if drops:
        msg = f"👞 【MR PORTER値下げ】{len(drops)}件\n⏰ {timestamp}\n\n" + "\n".join(drops[:5])
        send_line(msg)
    
    db.update(products)
    save_db(db)

if __name__ == "__main__":
    main()
