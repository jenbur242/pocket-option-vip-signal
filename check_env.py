#!/usr/bin/env python3
"""
Quick script to check if .env values are being read correctly
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("🔍 CHECKING .ENV CONFIGURATION")
print("=" * 60)

# Get values
trade_amount = os.getenv('TRADE_AMOUNT', 'NOT SET')
is_demo = os.getenv('IS_DEMO', 'NOT SET')
multiplier = os.getenv('MULTIPLIER', 'NOT SET')
martingale_step = os.getenv('MARTINGALE_STEP', 'NOT SET')

print(f"TRADE_AMOUNT: {trade_amount}")
print(f"IS_DEMO: {is_demo}")
print(f"MULTIPLIER: {multiplier}")
print(f"MARTINGALE_STEP: {martingale_step}")

print("\n" + "=" * 60)
print("📊 PARSED VALUES")
print("=" * 60)

try:
    amount = float(trade_amount)
    print(f"✅ Trade Amount: ${amount}")
except:
    print(f"❌ Trade Amount: Invalid value '{trade_amount}'")

try:
    demo = is_demo.lower() == 'true'
    print(f"✅ Account Type: {'DEMO' if demo else 'REAL'}")
except:
    print(f"❌ Account Type: Invalid value '{is_demo}'")

try:
    mult = float(multiplier)
    print(f"✅ Multiplier: {mult}x")
except:
    print(f"❌ Multiplier: Invalid value '{multiplier}'")

try:
    step = int(martingale_step)
    print(f"✅ Martingale Step: {step}")
except:
    print(f"❌ Martingale Step: Invalid value '{martingale_step}'")

print("\n" + "=" * 60)
print("💰 MARTINGALE CALCULATION")
print("=" * 60)

try:
    amount = float(trade_amount)
    mult = float(multiplier)
    step = int(martingale_step)
    
    print(f"Base Amount: ${amount}")
    print(f"Multiplier: {mult}x")
    print(f"Starting Step: {step}")
    print(f"\nTrade Amounts by Step:")
    for i in range(8):
        current = amount * (mult ** i)
        print(f"  Step {i}: ${current:.2f}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
