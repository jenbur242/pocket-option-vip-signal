import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from telethon.sync import TelegramClient

# Load environment variables
load_dotenv()

# Get credentials
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')

async def create_new_session():
    """Create a new Telegram session with unique name to avoid database lock"""
    
    if not API_ID or not API_HASH or not PHONE_NUMBER:
        print("Missing required environment variables:")
        print("   - TELEGRAM_API_ID")
        print("   - TELEGRAM_API_HASH") 
        print("   - TELEGRAM_PHONE")
        return
    
    # Create unique session name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_file = f'session_pocket_option_vip_{timestamp}'
    
    print("Creating new Telegram session...")
    print(f"   API ID: {API_ID}")
    print(f"   Phone: {PHONE_NUMBER}")
    print(f"   Session: {session_file}")
    
    # Create new session
    client = TelegramClient(session_file, API_ID, API_HASH)
    
    try:
        print("Starting authentication...")
        await client.start(PHONE_NUMBER)
        print("New session created successfully!")
        
        # Test connection
        me = await client.get_me()
        print(f"Logged in as: {me.first_name} {me.last_name or ''} (@{me.username})")
        
        # Test channel access
        try:
            channel = await client.get_entity('Pocket_Option_Signals_Vip')
            print(f"Can access channel: {channel.title}")
            print(f"Channel ID: {channel.id}")
        except Exception as e:
            print(f"Channel access test failed: {e}")
            print("   You may need to join the channel first")
        
        print(f"\nSession file created: {session_file}.session")
        print("Ready to deploy!")
        
        # Update main.py to use this new session
        await update_main_py_session(session_file)
        
    except Exception as e:
        print(f"Session creation failed: {e}")
        if "database is locked" in str(e).lower():
            print("\nDATABASE LOCK - Creating new session with timestamp...")
            print("This avoids conflicts with existing sessions.")
        else:
            print("Please check your credentials and try again")
    
    finally:
        try:
            await client.disconnect()
            print("Disconnected cleanly")
        except:
            pass

async def update_main_py_session(session_name):
    """Update main.py to use the new session name"""
    try:
        main_file = 'telegram/main.py'
        
        # Read current main.py
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update session name
        content = content.replace(
            "client = TelegramClient('session_pocket_option_vip', API_ID, API_HASH)",
            f"client = TelegramClient('{session_name}', API_ID, API_HASH)"
        )
        
        # Write back to main.py
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated main.py to use session: {session_name}")
        
    except Exception as e:
        print(f"Failed to update main.py: {e}")

if __name__ == "__main__":
    asyncio.run(create_new_session())
