#!/usr/bin/env python3
"""
Extract all configuration from .env file
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 80)
print("POCKET OPTION TRADING BOT - CONFIGURATION EXTRACT")
print("=" * 80)

# SSID Configuration
print("\nSSID CONFIGURATION")
print("-" * 40)
ssid_demo = os.getenv('SSID_DEMO')
ssid_real = os.getenv('SSID_REAL')
ssid_legacy = os.getenv('SSID')

if ssid_demo:
    print(f"SSID_DEMO: {ssid_demo[:80]}..." if len(ssid_demo) > 80 else f"SSID_DEMO: {ssid_demo}")
else:
    print("SSID_DEMO: NOT SET")

if ssid_real:
    print(f"SSID_REAL: {ssid_real[:80]}..." if len(ssid_real) > 80 else f"SSID_REAL: {ssid_real}")
else:
    print("SSID_REAL: NOT SET")

if ssid_legacy:
    print(f"SSID (legacy): {ssid_legacy[:80]}..." if len(ssid_legacy) > 80 else f"SSID (legacy): {ssid_legacy}")
else:
    print("SSID (legacy): NOT SET")

# Telegram Configuration
print("\nTELEGRAM CONFIGURATION")
print("-" * 40)
telegram_api_id = os.getenv('TELEGRAM_API_ID')
telegram_api_hash = os.getenv('TELEGRAM_API_HASH')
telegram_phone = os.getenv('TELEGRAM_PHONE')
telegram_channel = os.getenv('TELEGRAM_CHANNEL', 'testpob1234')
telegram_string_session = os.getenv('TELEGRAM_STRING_SESSION')

print(f"TELEGRAM_API_ID: {telegram_api_id or 'NOT SET'}")
if telegram_api_hash:
    print(f"TELEGRAM_API_HASH: {telegram_api_hash[:20]}..." if len(telegram_api_hash) > 20 else f"TELEGRAM_API_HASH: {telegram_api_hash}")
else:
    print("TELEGRAM_API_HASH: NOT SET")
print(f"TELEGRAM_PHONE: {telegram_phone or 'NOT SET'}")
print(f"TELEGRAM_CHANNEL: {telegram_channel}")
if telegram_string_session:
    print(f"TELEGRAM_STRING_SESSION: {telegram_string_session[:30]}..." if len(telegram_string_session) > 30 else f"TELEGRAM_STRING_SESSION: {telegram_string_session}")
else:
    print("TELEGRAM_STRING_SESSION: NOT SET")

# Trading Configuration
print("\nTRADING CONFIGURATION")
print("-" * 40)
trade_amount = os.getenv('TRADE_AMOUNT', '1.0')
is_demo = os.getenv('IS_DEMO', 'True')
multiplier = os.getenv('MULTIPLIER', '2.5')
martingale_step = os.getenv('MARTINGALE_STEP', '0')

print(f"TRADE_AMOUNT: ${trade_amount}")
print(f"IS_DEMO: {is_demo}")
print(f"MULTIPLIER: {multiplier}x")
print(f"MARTINGALE_STEP: {martingale_step}")

# Calculate martingale amounts
try:
    amount = float(trade_amount)
    mult = float(multiplier)
    step = int(martingale_step)
    
    print(f"\nMARTINGALE CALCULATION")
    print("-" * 40)
    print(f"Base Amount: ${amount:.2f}")
    print(f"Multiplier: {mult}x")
    print(f"Starting Step: {step}")
    print(f"\nTrade Amounts by Step:")
    for i in range(8):
        current = amount * (mult ** i)
        print(f"  Step {i}: ${current:.2f}")
    
    current_amount = amount * (mult ** step)
    print(f"\nCurrent Trade Amount (Step {step}): ${current_amount:.2f}")
    
except Exception as e:
    print(f"Error calculating martingale: {e}")

# Railway Configuration (if exists)
print("\nRAILWAY CONFIGURATION")
print("-" * 40)
railway_env = os.getenv('RAILWAY_ENVIRONMENT')
railway_port = os.getenv('PORT', '5000')

print(f"RAILWAY_ENVIRONMENT: {railway_env or 'NOT SET'}")
print(f"PORT: {railway_port}")

# Session Management
print("\nSESSION MANAGEMENT")
print("-" * 40)
session_files = []
if os.path.exists('po_vip_testing.session'):
    session_files.append('po_vip_testing.session')
if os.path.exists('po_vip_testing.session-journal'):
    session_files.append('po_vip_testing.session-journal')

print(f"Session files found: {len(session_files)}")
for file in session_files:
    print(f"  - {file}")

print("\n" + "=" * 80)
print("CONFIGURATION EXTRACT COMPLETE")
print("=" * 80)
