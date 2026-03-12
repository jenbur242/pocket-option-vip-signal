#!/usr/bin/env python3
"""
Railway OTP Handler - Complete string session creation
Use this after receiving OTP from railway_session_manager.py
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

async def complete_string_session(otp_code):
    """Complete string session creation with OTP"""
    
    if not API_ID or not API_HASH or not PHONE_NUMBER:
        print("❌ Missing required environment variables")
        return False
    
    # Load session status
    session_file = 'railway_session_status.json'
    session_name = None
    
    try:
        if os.path.exists(session_file):
            import json
            with open(session_file, 'r') as f:
                status = json.load(f)
                session_name = status.get('session_name')
        
        if not session_name:
            print("❌ No pending session found. Run railway_session_manager.py first")
            return False
        
        print(f"🔍 Completing session: {session_name}")
        print(f"📱 Phone: {PHONE_NUMBER}")
        print(f"🔑 OTP Code: {otp_code}")
        
        # Connect and complete sign in
        client = TelegramClient(session_name, API_ID, API_HASH)
        
        await client.connect()
        
        try:
            await client.sign_in(PHONE_NUMBER, otp_code)
            print("✅ OTP verified successfully!")
            
            # Convert to string session
            string_session = StringSession.save(client.session)
            
            # Save to .env file
            env_path = os.path.join(os.path.dirname(__file__), '.env')
            set_key(env_path, 'TELEGRAM_STRING_SESSION', string_session)
            load_dotenv(override=True)
            
            # Update status
            status_data = {
                'status': 'created',
                'created': datetime.now().isoformat(),
                'last_check': datetime.now().isoformat(),
                'string_session_length': len(string_session)
            }
            
            with open(session_file, 'w') as f:
                import json
                json.dump(status_data, f, indent=2)
            
            print(f"✅ String session saved to .env!")
            print(f"📁 Path: {env_path}")
            print("🎉 Ready for Railway deployment!")
            print("\n📋 NEXT STEPS:")
            print("1️⃣ Your .env file now has TELEGRAM_STRING_SESSION")
            print("2️⃣ Deploy to Railway")
            print("3️⃣ Bot will work automatically with string session")
            
            await client.disconnect()
            
            # Clean up temporary files
            temp_files = [f"{session_name}.session", f"{session_name}.session-journal"]
            for file in temp_files:
                if os.path.exists(file):
                    os.remove(file)
                    print(f"🗑️ Cleaned up: {file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Invalid OTP code: {e}")
            await client.disconnect()
            return False
            
    except Exception as e:
        print(f"❌ Error completing session: {e}")
        return False

if __name__ == "__main__":
    import sys
    from datetime import datetime
    
    if len(sys.argv) != 2:
        print("🚨 Railway OTP Handler")
        print("=" * 40)
        print("Usage: python railway_otp_handler.py <OTP_CODE>")
        print("\nExample: python railway_otp_handler.py 12345")
        print("\n💡 Run this after getting OTP from railway_session_manager.py")
        sys.exit(1)
    
    otp_code = sys.argv[1].strip()
    
    print("=" * 50)
    print("🤖 RAILWAY OTP HANDLER")
    print("=" * 50)
    
    asyncio.run(complete_string_session(otp_code))
