# MR PORTER メンズシューズ値下げ監視 - 値下げ時のみ通知（2時間ごと）

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
        print(f"✅ LINE送信: {r.status_code}")
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

def fetch_mrporter_shoes():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        r = requests.get(MRPORTER_URL, headers=headers, timeout=15)
        soup = BeautifulSoup(r.content, 'html.parser')
        products = {}
        
        # MR PORTER商品セレクタ
        items = soup.find_all('div', class_=['product-tile', 'product', 'item'])
        for item in items[:30]:
            try:
                name_elem = item.find(['h3', 'h2', 'a', '.product-name'])
                if not name_elem:
                    continue
                name = name_elem.get_text(strip=True)[:50]
                
                # 価格抽出（$）
                price_text = ''
                price_elems = item.find_all(string=re.compile(r'\$\d+'))
                if price_elems:
                    price_text = price_elems[0]
                
                price_match = re.search(r'[\$]?([\d,]+\.?\d*)', price_text)
                if price_match:
                    price = int(float(price_match.group(1).replace(',', '')) * 100)  # セント単位
                    products[name] = price
            except:
                continue
        
        print(f"👞 MR PORTER商品数: {len(products)}")
        return products
    except Exception as e:
        print(f"❌ MR PORTERエラー: {e}")
        return {}

def main():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S JST')
    db = load_db()
    
    current_products = fetch_mrporter_shoes()
    if not current_products:
        return
    
    # 値下げ検知（値下げ時のみ通知）
    price_drops = []
    for name, price in current_products.items():
        if name in db and db[name] > price:
            drop_amount = (db[name] - price) / 100  # ドルに戻す
            price_drops.append({
                'name': name[:35],
                'old': f"${db[name]/100:.0f}",
                'new': f"${price/100:.0f}",
                'drop': f"${drop_amount:.0f}"
            })
    
    # 値下げがあった時のみ通知
    if price_drops:
        message = f"🔥 【MR PORTER値下げ】{len(price_drops)}件\n⏰ {timestamp}\n\n"
        for drop in sorted(price_drops, key=lambda x: float(x['drop'][1:]), reverse=True)[:5]:
            message += f"👞 {drop['name']}\n"
            message += f"   {drop['old']} → {drop['new']}\n"
            message += f"   ↓ {drop['drop']}\n\n"
        message += f"🔗 {MRPORTER_URL}"
        send_line(message)
        print(f"✅ MR PORTER値下げ通知: {len(price_drops)}件")
    else:
        print("📊 MR PORTER値下げなし")
    
    # DB更新
    db.update(current_products)
    save_db(db)
    print("✅ MR PORTER監視完了")

if __name__ == "__main__":
    main()
