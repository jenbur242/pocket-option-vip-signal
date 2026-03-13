#!/usr/bin/env python3
"""
Check Railway app status
"""

import requests
import json

def check_railway_status():
    try:
        response = requests.get('https://pocket-option-vip-signal-production.up.railway.app/status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("=== RAILWAY BOT STATUS ===")
            print(f"Running: {data.get('running', False)}")
            print(f"Telegram Connected: {data.get('telegram_connected', False)}")
            print(f"PocketOption Connected: {data.get('pocketoption_connected', False)}")
            print(f"Balance: ${data.get('current_balance', 0):.2f}")
            print(f"Total Trades: {data.get('total_trades', 0)}")
            print(f"Started At: {data.get('started_at', 'N/A')}")
            print("==========================")
        else:
            print(f"Error: HTTP {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_railway_status()
