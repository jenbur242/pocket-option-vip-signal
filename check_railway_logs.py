#!/usr/bin/env python3
"""
Check Railway logs for duration
"""

import requests
import json

def check_duration():
    try:
        response = requests.get('https://pocket-option-vip-signal-production.up.railway.app/logs', timeout=10)
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            
            print("=== RECENT RAILWAY LOGS ===")
            for i, log in enumerate(logs[-20:], 1):
                message = log.get('message', '')
                if 'min' in message or 'Duration' in message:
                    print(f"{i}. {message}")
            
            print("=== DURATION ANALYSIS ===")
            duration_logs = [log for log in logs if 'min' in log.get('message', '')]
            print(f"Found {len(duration_logs)} logs with duration info")
            
            # Look for default duration message
            for log in logs:
                message = log.get('message', '')
                if 'Default Duration' in message:
                    print(f"Default duration log: {message}")
                    if '1 minute' in message:
                        print("✅ CORRECT: Default is 1 minute")
                    elif '2 minutes' in message:
                        print("❌ INCORRECT: Default is 2 minutes")
                    else:
                        print("❓ UNKNOWN: Default duration unclear")
                        
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_duration()
