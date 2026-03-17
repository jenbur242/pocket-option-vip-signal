#!/usr/bin/env python3
"""
Simple health check for Railway deployment
"""

import os
import asyncio
from datetime import datetime

def log_message(message: str):
    """Log with timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[HEALTH] {timestamp} - {message}")

async def check_bot_health():
    """Check if bot is healthy"""
    try:
        # Check if main.py can be imported
        import main
        log_message("Main module imported successfully")
        
        # Check configuration
        trade_amount = main.get_trade_amount()
        multiplier = main.get_multiplier()
        is_demo = main.get_is_demo()
        
        log_message(f"Trade amount: ${trade_amount}")
        log_message(f"Multiplier: {multiplier}x")
        log_message(f"Demo mode: {is_demo}")
        
        # Check if session is available
        string_session = os.getenv('STRING_SESSION', '')
        ssid_demo = os.getenv('SSID_DEMO', '')
        
        if string_session and ssid_demo:
            log_message("Session credentials available")
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "bot_running": False,
                "service": "pocket-option-trading-bot",
                "config_loaded": True
            }
        else:
            log_message("Session credentials missing")
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "bot_running": False,
                "service": "pocket-option-trading-bot",
                "error": "Session credentials not configured"
            }
            
    except Exception as e:
        log_message(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "bot_running": False,
            "service": "pocket-option-trading-bot",
            "error": str(e)
        }

async def main():
    """Main health check"""
    log_message("Starting health check...")
    
    # Set up environment
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    os.environ.setdefault('PYTHONUNBUFFERED', '1')
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check health
    result = await check_bot_health()
    
    # Return JSON response
    import json
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
