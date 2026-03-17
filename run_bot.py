#!/usr/bin/env python3
"""
Direct Bot Runner - Uses .env configuration and runs main.py directly
"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def log_message(message: str):
    """Log with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[BOT] {timestamp} - {message}")

def load_config():
    """Load configuration from environment"""
    config = {}
    
    # Trading configuration
    config['TRADE_AMOUNT'] = float(os.getenv('TRADE_AMOUNT', '5.0'))
    config['MULTIPLIER'] = float(os.getenv('MULTIPLIER', '2.5'))
    config['IS_DEMO'] = os.getenv('IS_DEMO', 'true').lower() == 'true'
    config['INITIAL_BALANCE'] = float(os.getenv('INITIAL_BALANCE', '10000.0'))
    
    # Telegram configuration
    config['API_ID'] = os.getenv('API_ID')
    config['API_HASH'] = os.getenv('API_HASH')
    config['PHONE_NUMBER'] = os.getenv('PHONE_NUMBER')
    config['STRING_SESSION'] = os.getenv('STRING_SESSION')
    
    # PocketOption SSIDs
    config['SSID_DEMO'] = os.getenv('SSID_DEMO')
    config['SSID_REAL'] = os.getenv('SSID_REAL')
    
    # Bot configuration
    config['AUTO_START'] = os.getenv('AUTO_START', 'false').lower() == 'true'
    config['BOT_ENABLED'] = os.getenv('BOT_ENABLED', 'true').lower() == 'true'
    config['LOG_LEVEL'] = os.getenv('LOG_LEVEL', 'INFO')
    
    # Railway configuration
    config['PORT'] = os.getenv('PORT', '8000')
    config['RAILWAY_ENVIRONMENT'] = os.getenv('RAILWAY_ENVIRONMENT', 'development')
    
    return config

def display_config(config):
    """Display current configuration"""
    log_message("=== BOT CONFIGURATION ===")
    log_message(f"Trade Amount: ${config['TRADE_AMOUNT']}")
    log_message(f"Multiplier: {config['MULTIPLIER']}x")
    log_message(f"Demo Mode: {config['IS_DEMO']}")
    log_message(f"Initial Balance: ${config['INITIAL_BALANCE']}")
    log_message(f"Auto Start: {config['AUTO_START']}")
    log_message(f"Bot Enabled: {config['BOT_ENABLED']}")
    log_message(f"Environment: {config['RAILWAY_ENVIRONMENT']}")
    log_message(f"Port: {config['PORT']}")
    
    # Check critical configurations
    if not config['STRING_SESSION']:
        log_message("[WARNING] STRING_SESSION not set")
    if not config['SSID_DEMO']:
        log_message("[WARNING] SSID_DEMO not set")
    if not config['API_ID']:
        log_message("[WARNING] API_ID not set")
    if not config['API_HASH']:
        log_message("[WARNING] API_HASH not set")
    
    log_message("========================")

def update_main_py_globals(config):
    """Update main.py global variables with config"""
    # This is a simple approach - we'll modify main.py to use environment
    log_message("Updating main.py configuration...")
    
    # Create a config module that main.py can import
    config_content = f'''# Auto-generated configuration from run_bot.py
import os

# Trading Configuration
TRADE_AMOUNT = {config['TRADE_AMOUNT']}
MULTIPLIER = {config['MULTIPLIER']}
IS_DEMO = {str(config['IS_DEMO']).lower()}
INITIAL_BALANCE = {config['INITIAL_BALANCE']}

# Telegram Configuration  
API_ID = {config['API_ID']}
API_HASH = "{config['API_HASH']}"
PHONE_NUMBER = "{config['PHONE_NUMBER']}"
STRING_SESSION = "{config['STRING_SESSION']}"

# PocketOption SSIDs
SSID_DEMO = "{config['SSID_DEMO']}"
SSID_REAL = "{config['SSID_REAL']}"

# Bot Configuration
AUTO_START = {str(config['AUTO_START']).lower()}
BOT_ENABLED = {str(config['BOT_ENABLED']).lower()}
LOG_LEVEL = "{config['LOG_LEVEL']}"
'''
    
    # Write to config.py
    with open('config.py', 'w') as f:
        f.write(config_content)
    
    log_message("Configuration saved to config.py")
    return True

async def run_main():
    """Run the main bot"""
    try:
        log_message("Starting main.py...")
        
        # Import and run main
        import main
        await main.main()
        
    except KeyboardInterrupt:
        log_message("Bot stopped by user")
    except Exception as e:
        log_message(f"Bot error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main runner function"""
    log_message("=== Pocket Option Bot Runner ===")
    
    # Load configuration
    config = load_config()
    
    # Display configuration
    display_config(config)
    
    # Check if bot is enabled
    if not config['BOT_ENABLED']:
        log_message("Bot is disabled in configuration")
        return
    
    # Update main.py globals
    if not update_main_py_globals(config):
        log_message("Failed to update configuration")
        return
    
    # Run the bot
    try:
        asyncio.run(run_main())
    except KeyboardInterrupt:
        log_message("Runner stopped by user")
    except Exception as e:
        log_message(f"Runner error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
