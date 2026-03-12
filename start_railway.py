#!/usr/bin/env python3
"""
Railway-Ready Startup Script
Handles all Railway deployment requirements and error recovery
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_railway_environment():
    """Check if Railway environment is properly configured"""
    logger.info("🔍 Checking Railway environment...")
    
    # Check essential environment variables
    required_vars = [
        'TELEGRAM_API_ID',
        'TELEGRAM_API_HASH', 
        'TELEGRAM_PHONE',
        'TELEGRAM_STRING_SESSION',
        'SSID_DEMO',
        'TRADE_AMOUNT',
        'IS_DEMO',
        'MULTIPLIER'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var).strip() == '':
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        logger.error("💡 Add these to Railway Dashboard > Variables")
        return False
    
    logger.info("✅ All required environment variables found")
    return True

async def test_telegram_session():
    """Test if Telegram session is valid"""
    logger.info("🔍 Testing Telegram session...")
    
    try:
        from telethon.sync import TelegramClient
        from telethon.sessions import StringSession
        
        api_id = int(os.getenv('TELEGRAM_API_ID'))
        api_hash = os.getenv('TELEGRAM_API_HASH')
        string_session = os.getenv('TELEGRAM_STRING_SESSION')
        
        client = TelegramClient(StringSession(string_session), api_id, api_hash)
        await client.connect()
        
        if await client.is_user_authorized():
            me = await client.get_me()
            logger.info(f"✅ Telegram session valid - User: @{me.username}")
            await client.disconnect()
            return True
        else:
            logger.error("❌ Telegram session not authorized")
            await client.disconnect()
            return False
            
    except Exception as e:
        logger.error(f"❌ Telegram session test failed: {e}")
        return False

async def test_pocket_option_connection():
    """Test Pocket Option connection"""
    logger.info("🔍 Testing Pocket Option connection...")
    
    try:
        from pocketoptionapi_async import AsyncPocketOptionClient
        
        ssid_demo = os.getenv('SSID_DEMO')
        is_demo = os.getenv('IS_DEMO', 'True').lower() == 'true'
        
        client = AsyncPocketOptionClient(ssid=ssid_demo, is_demo=is_demo)
        await client.connect()
        
        balance = await client.get_balance()
        logger.info(f"✅ Pocket Option connected - Balance: ${balance}")
        
        await client.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"❌ Pocket Option connection failed: {e}")
        return False

def start_api_server():
    """Start API server with error handling"""
    logger.info("🌐 Starting API server...")
    
    try:
        # Import and start API server
        from api_server import app
        
        # Use Railway port
        port = int(os.getenv('PORT', 5000))
        
        logger.info(f"🚀 Starting server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        logger.error(f"❌ Failed to start API server: {e}")
        return False

async def start_bot():
    """Start the trading bot"""
    logger.info("🤖 Starting trading bot...")
    
    try:
        from telegram.main import main as telegram_main
        await telegram_main()
        
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        return False

def create_auto_session_if_needed():
    """Create auto session if none exists"""
    logger.info("🔄 Checking if auto-session is needed...")
    
    # Check if string session exists
    string_session = os.getenv('TELEGRAM_STRING_SESSION')
    
    if not string_session or string_session.strip() == '':
        logger.warning("⚠️ No string session found, starting auto-session creation...")
        
        try:
            # Start auto-session creation
            import subprocess
            result = subprocess.run([
                sys.executable, 'railway_auto_session.py'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                logger.info("✅ Auto-session creation started")
                logger.info("📨 Check Railway logs for OTP code")
                logger.info("💡 Complete via API: POST /api/sessions/complete-auto")
                return True
            else:
                logger.error(f"❌ Auto-session creation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Auto-session creation timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Auto-session creation error: {e}")
            return False
    else:
        logger.info("✅ String session found")
        return True

async def main():
    """Main startup function for Railway"""
    logger.info("=" * 60)
    logger.info("🚀 RAILWAY DEPLOYMENT STARTUP")
    logger.info("=" * 60)
    logger.info(f"📅 Started at: {datetime.now().isoformat()}")
    
    # Step 1: Check environment
    if not check_railway_environment():
        logger.error("❌ Environment check failed - aborting startup")
        sys.exit(1)
    
    # Step 2: Create auto-session if needed
    if not create_auto_session_if_needed():
        logger.error("❌ Auto-session creation failed")
        logger.info("💡 Manual setup required:")
        logger.info("   1. Run locally: python railway_session_manager.py")
        logger.info("   2. Complete OTP: python railway_otp_handler.py <OTP_CODE>")
        logger.info("   3. Add TELEGRAM_STRING_SESSION to Railway environment")
        sys.exit(1)
    
    # Step 3: Test connections
    logger.info("🔍 Testing connections...")
    
    # Test Telegram session
    telegram_ok = await test_telegram_session()
    if not telegram_ok:
        logger.error("❌ Telegram session test failed")
        logger.info("💡 Check TELEGRAM_STRING_SESSION in Railway environment")
        sys.exit(1)
    
    # Test Pocket Option
    pocket_ok = await test_pocket_option_connection()
    if not pocket_ok:
        logger.error("❌ Pocket Option connection test failed")
        logger.info("💡 Check SSID_DEMO in Railway environment")
        sys.exit(1)
    
    # Step 4: Start services
    logger.info("🚀 All tests passed - starting services...")
    
    # Start API server (this will run in the main thread)
    logger.info("🌐 Starting API server...")
    start_api_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Shutting down...")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
