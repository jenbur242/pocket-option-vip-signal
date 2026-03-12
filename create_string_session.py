#!/usr/bin/env python3
"""
Quick String Session Creator for Pocket Option Bot
Creates a string session and saves it to .env file
"""

import os
import asyncio
from dotenv import load_dotenv, set_key
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# Load environment variables
load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')

async def create_string_session():
    """Create a string session and save to .env"""
    
    if not API_ID or not API_HASH or not PHONE_NUMBER:
        print("❌ Missing required environment variables:")
        print("   - TELEGRAM_API_ID")
        print("   - TELEGRAM_API_HASH") 
        print("   - TELEGRAM_PHONE")
        print("\n📝 Please check your .env file")
        return
    
    print("🔐 Creating Telegram string session...")
    print(f"📱 Phone: {PHONE_NUMBER}")
    print(f"🔑 API ID: {API_ID}")
    print(f"🔒 API Hash: {API_HASH[:8]}...{API_HASH[-8:]}")
    
    try:
        # Create client with unique session name
        client = TelegramClient('temp_string_session', API_ID, API_HASH)
        
        print("\n📱 Connecting to Telegram...")
        await client.connect()
        
        if not await client.is_user_authorized():
            print("🔑 Sending code to your phone...")
            await client.send_code_request(PHONE_NUMBER)
            
            # Get code from user
            code = input("\n📨 Enter the OTP code you received: ").strip()
            
            try:
                await client.sign_in(PHONE_NUMBER, code)
                print("✅ Successfully signed in!")
            except Exception as e:
                print(f"❌ Invalid code: {e}")
                await client.disconnect()
                return
        else:
            print("✅ Already authorized!")
        
        # Convert to string session
        print("🔄 Converting to string session...")
        string_session = StringSession.save(client.session)
        
        # Save to .env file
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        set_key(env_path, 'TELEGRAM_STRING_SESSION', string_session)
        
        print(f"✅ String session saved to .env file!")
        print(f"📁 Path: {env_path}")
        print("\n🎉 You can now run the bot!")
        print("💡 The bot will use this string session automatically")
        
        # Clean up
        await client.disconnect()
        
        # Delete temporary session files
        temp_files = ['temp_string_session.session', 'temp_string_session.session-journal']
        for file in temp_files:
            if os.path.exists(file):
                os.remove(file)
        
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        print("\n💡 Possible solutions:")
        print("   1. Check your internet connection")
        print("   2. Verify phone number format (+countrycode)")
        print("   3. Make sure Telegram API credentials are correct")

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 POCKET OPTION - STRING SESSION CREATOR")
    print("=" * 60)
    
    asyncio.run(create_string_session())
