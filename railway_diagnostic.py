#!/usr/bin/env python3
"""
Railway Diagnostic Script
Run this on Railway to see what environment variables are set
"""
import os
import sys

print("=" * 80)
print("🔍 RAILWAY ENVIRONMENT DIAGNOSTIC")
print("=" * 80)
print()

# Check if running on Railway
is_railway = os.getenv('RAILWAY_ENVIRONMENT') is not None
print(f"Running on Railway: {'YES ✅' if is_railway else 'NO ❌ (Local)'}")
print()

print("=" * 80)
print("📊 TRADING CONFIGURATION")
print("=" * 80)

# Get all trading-related environment variables
env_vars = {
    'TRADE_AMOUNT': os.getenv('TRADE_AMOUNT', 'NOT SET'),
    'IS_DEMO': os.getenv('IS_DEMO', 'NOT SET'),
    'MULTIPLIER': os.getenv('MULTIPLIER', 'NOT SET'),
    'MARTINGALE_STEP': os.getenv('MARTINGALE_STEP', 'NOT SET'),
}

for key, value in env_vars.items():
    status = '✅' if value != 'NOT SET' else '❌'
    print(f"{status} {key:20} = {value}")

print()
print("=" * 80)
print("💰 PARSED VALUES")
print("=" * 80)

try:
    trade_amount = float(os.getenv('TRADE_AMOUNT', '1.0'))
    print(f"✅ Trade Amount: ${trade_amount}")
    
    if trade_amount == 1.0:
        print("   ⚠️  WARNING: Using default value of $1.0")
        print("   ⚠️  TRADE_AMOUNT environment variable may not be set correctly")
    elif trade_amount == 5.0:
        print("   ✅ Correct! Using $5.0 as configured")
    
except Exception as e:
    print(f"❌ Error parsing TRADE_AMOUNT: {e}")

try:
    is_demo = os.getenv('IS_DEMO', 'True').lower() == 'true'
    print(f"✅ Account Type: {'DEMO' if is_demo else 'REAL'}")
except Exception as e:
    print(f"❌ Error parsing IS_DEMO: {e}")

try:
    multiplier = float(os.getenv('MULTIPLIER', '2.5'))
    print(f"✅ Multiplier: {multiplier}x")
except Exception as e:
    print(f"❌ Error parsing MULTIPLIER: {e}")

try:
    step = int(os.getenv('MARTINGALE_STEP', '0'))
    print(f"✅ Starting Step: {step}")
except Exception as e:
    print(f"❌ Error parsing MARTINGALE_STEP: {e}")

print()
print("=" * 80)
print("🎯 MARTINGALE PREVIEW")
print("=" * 80)

try:
    trade_amount = float(os.getenv('TRADE_AMOUNT', '1.0'))
    multiplier = float(os.getenv('MULTIPLIER', '2.5'))
    
    print(f"Base Amount: ${trade_amount}")
    print(f"Multiplier: {multiplier}x")
    print()
    print("Trade amounts by step:")
    for i in range(8):
        amount = trade_amount * (multiplier ** i)
        print(f"  Step {i}: ${amount:>10.2f}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=" * 80)
print("🔧 TROUBLESHOOTING")
print("=" * 80)

if os.getenv('TRADE_AMOUNT') is None:
    print("❌ TRADE_AMOUNT is NOT SET in environment variables")
    print("   → Go to Railway Dashboard → Variables")
    print("   → Add: TRADE_AMOUNT = 5")
elif os.getenv('TRADE_AMOUNT') == '1':
    print("⚠️  TRADE_AMOUNT is set to '1' (should be '5')")
    print("   → Go to Railway Dashboard → Variables")
    print("   → Change TRADE_AMOUNT from 1 to 5")
elif os.getenv('TRADE_AMOUNT') == '5':
    print("✅ TRADE_AMOUNT is correctly set to '5'")
else:
    print(f"ℹ️  TRADE_AMOUNT is set to: {os.getenv('TRADE_AMOUNT')}")

print()
print("=" * 80)
print("📝 INSTRUCTIONS")
print("=" * 80)
print()
print("To fix TRADE_AMOUNT on Railway:")
print("1. Go to https://railway.app")
print("2. Select your project")
print("3. Click 'Variables' tab")
print("4. Find TRADE_AMOUNT")
print("5. Change value from '1' to '5'")
print("6. Save (auto-saves)")
print("7. Redeploy (automatic)")
print()
print("=" * 80)
