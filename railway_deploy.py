#!/usr/bin/env python3
"""
Railway-Ready Startup Script
Automatic session management for Railway deployment
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_STRING_SESSION = os.getenv('TELEGRAM_STRING_SESSION')

def check_railway_readiness():
    """Check if the bot is ready for Railway deployment"""
    print("🚀 RAILWAY DEPLOYMENT CHECK")
    print("=" * 50)
    
    # Check essential environment variables
    required_vars = {
        'TELEGRAM_API_ID': os.getenv('TELEGRAM_API_ID'),
        'TELEGRAM_API_HASH': os.getenv('TELEGRAM_API_HASH'),
        'TELEGRAM_PHONE': os.getenv('TELEGRAM_PHONE'),
        'TELEGRAM_STRING_SESSION': TELEGRAM_STRING_SESSION,
        'SSID_DEMO': os.getenv('SSID_DEMO'),
        'TRADE_AMOUNT': os.getenv('TRADE_AMOUNT'),
        'IS_DEMO': os.getenv('IS_DEMO'),
        'MULTIPLIER': os.getenv('MULTIPLIER')
    }
    
    all_ready = True
    
    print("📋 Environment Variables Status:")
    for var_name, var_value in required_vars.items():
        if var_value:
            if var_name == 'TELEGRAM_STRING_SESSION':
                masked_value = var_value[:20] + "..." if len(var_value) > 20 else "***SET***"
                print(f"   ✅ {var_name}: {masked_value}")
            elif var_name == 'TELEGRAM_API_HASH':
                print(f"   ✅ {var_name}: ...{var_value[-8:]}")
            else:
                print(f"   ✅ {var_name}: {var_value}")
        else:
            print(f"   ❌ {var_name}: NOT SET")
            all_ready = False
    
    print("\n" + "=" * 50)
    
    if all_ready:
        print("🎉 RAILWAY DEPLOYMENT READY!")
        print("\n✅ All required environment variables are set")
        print("✅ String session is configured")
        print("✅ Bot will work automatically on Railway")
        
        print("\n📋 DEPLOYMENT INSTRUCTIONS:")
        print("1️⃣ Copy all variables from .env.railway to Railway Dashboard")
        print("2️⃣ Deploy your bot to Railway")
        print("3️⃣ Bot will start automatically with string session")
        print("4️⃣ No manual intervention needed!")
        
        print("\n🔧 BOT FEATURES ON RAILWAY:")
        print("   • Automatic Telegram connection via string session")
        print("   • No session file issues")
        print("   • 24/7 operation")
        print("   • Automatic session cleanup")
        print("   • Railway persistent storage")
        
    else:
        print("❌ NOT READY FOR RAILWAY")
        print("\n📝 MISSING CONFIGURATION:")
        
        if not TELEGRAM_STRING_SESSION:
            print("   🔑 String session missing")
            print("   💡 Run: python railway_session_manager.py")
            print("   💡 Then: python railway_otp_handler.py <OTP_CODE>")
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        for var in missing_vars:
            print(f"   ❌ {var} not configured")
        
        print("\n🔧 SETUP STEPS:")
        print("1️⃣ Set missing environment variables in .env")
        print("2️⃣ Create string session using railway_session_manager.py")
        print("3️⃣ Complete OTP verification with railway_otp_handler.py")
        print("4️⃣ Run this check again to verify readiness")
    
    return all_ready

def show_railway_env_template():
    """Show Railway environment variables template"""
    print("\n" + "=" * 50)
    print("📋 RAILWAY ENVIRONMENT VARIABLES TEMPLATE")
    print("=" * 50)
    
    env_vars = {
        'TELEGRAM_API_ID': os.getenv('TELEGRAM_API_ID', 'your_api_id'),
        'TELEGRAM_API_HASH': os.getenv('TELEGRAM_API_HASH', 'your_api_hash'),
        'TELEGRAM_PHONE': os.getenv('TELEGRAM_PHONE', '+1234567890'),
        'TELEGRAM_STRING_SESSION': TELEGRAM_STRING_SESSION[:50] + "..." if TELEGRAM_STRING_SESSION else 'generated_string_session',
        'SSID_DEMO': os.getenv('SSID_DEMO', 'your_ssid_demo'),
        'SSID_REAL': os.getenv('SSID_REAL', 'your_ssid_real'),
        'TRADE_AMOUNT': os.getenv('TRADE_AMOUNT', '5'),
        'IS_DEMO': os.getenv('IS_DEMO', 'True'),
        'MULTIPLIER': os.getenv('MULTIPLIER', '2.5'),
        'MARTINGALE_STEP': os.getenv('MARTINGALE_STEP', '0'),
        'TELEGRAM_CHANNEL': os.getenv('TELEGRAM_CHANNEL', 'your_channel_username')
    }
    
    print("Copy these to Railway Dashboard > Variables:\n")
    
    for var_name, var_value in env_vars.items():
        if var_name == 'TELEGRAM_STRING_SESSION' and var_value != 'generated_string_session':
            print(f"{var_name}={var_value}")
        elif var_name == 'TELEGRAM_API_HASH':
            print(f"{var_name}=your_api_hash")
        else:
            print(f"{var_name}={var_value}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--template':
        show_railway_env_template()
    else:
        ready = check_railway_readiness()
        
        if not ready:
            print(f"\n💡 Need help? Run: python {sys.argv[0]} --template")
            print("💡 This will show the environment variables template")
