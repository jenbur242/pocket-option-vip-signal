import asyncio
import os
from dotenv import load_dotenv
from telethon.sync import TelegramClient

# Load environment variables
load_dotenv()

# Get credentials
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')

async def create_new_session():
    """Create a new Telegram session"""
    
    if not API_ID or not API_HASH or not PHONE_NUMBER:
        print("❌ Missing required environment variables:")
        print("   - TELEGRAM_API_ID")
        print("   - TELEGRAM_API_HASH") 
        print("   - TELEGRAM_PHONE")
        return
    
    print("🔧 Creating new Telegram session...")
    print(f"   API ID: {API_ID}")
    print(f"   Phone: {PHONE_NUMBER}")
    print(f"   Session: session_pocket_option_vip")
    
    # Create new session
    client = TelegramClient('session_pocket_option_vip', API_ID, API_HASH)
    
    try:
        await client.start(PHONE_NUMBER)
        print("✅ New session created successfully!")
        
        # Test connection
        me = await client.get_me()
        print(f"👤 Logged in as: {me.first_name} {me.last_name or ''} (@{me.username})")
        
        # Test channel access
        try:
            channel = await client.get_entity('Pocket_Option_Signals_Vip')
            print(f"✅ Can access channel: {channel.title}")
        except Exception as e:
            print(f"⚠️ Channel access test failed: {e}")
        
    except Exception as e:
        print(f"❌ Session creation failed: {e}")
        print("Please check your credentials and try again")
    
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(create_new_session())
