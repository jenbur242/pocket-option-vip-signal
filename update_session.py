#!/usr/bin/env python3
"""
Script to update Telegram session string
Run this script and enter OTP when prompted
"""

import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# Your credentials
API_ID = 34506083
API_HASH = '5676893fa1c0fe15eca5dbbceb3ab6a2'
PHONE_NUMBER = '+12428018500'

async def update_session():
    """Update session string with fresh authentication"""
    print("=== Telegram Session Update ===")
    print(f"Phone: {PHONE_NUMBER}")
    print(f"API ID: {API_ID}")
    print()
    
    # Create temporary client
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    
    try:
        await client.connect()
        print("✅ Connected to Telegram")
        
        if not await client.is_user_authorized():
            print("📱 Sending OTP code...")
            await client.send_code_request(PHONE_NUMBER)
            
            # Get OTP from user
            otp_code = input("Enter the OTP code you received: ").strip()
            
            if not otp_code:
                print("❌ No OTP entered")
                return
                
            # Sign in with OTP
            await client.sign_in(PHONE_NUMBER, otp_code)
            print("✅ Successfully signed in!")
        else:
            print("✅ Already authorized")
        
        # Get new session string
        session_string = StringSession.save(client.session)
        print("\n" + "="*50)
        print("🔑 NEW SESSION STRING:")
        print("="*50)
        print(session_string)
        print("="*50)
        print("\nCopy this string and update main.py line 39")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        try:
            await client.disconnect()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(update_session())
