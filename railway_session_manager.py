#!/usr/bin/env python3
"""
Railway-Ready Telegram Session Manager
Automatic string session creation and management for Railway deployment
"""

import os
import asyncio
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv, set_key
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# Load environment variables
load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')

class RailwaySessionManager:
    def __init__(self):
        self.env_path = os.path.join(os.path.dirname(__file__), '.env')
        self.session_file = 'railway_session_status.json'
        
    def load_session_status(self):
        """Load session status from file"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {'created': None, 'last_check': None, 'status': 'none'}
    
    def save_session_status(self, status_data):
        """Save session status to file"""
        try:
            with open(self.session_file, 'w') as f:
                json.dump(status_data, f, indent=2)
        except Exception as e:
            print(f"Failed to save session status: {e}")
    
    def has_valid_string_session(self):
        """Check if we have a valid string session"""
        string_session = os.getenv('TELEGRAM_STRING_SESSION')
        if not string_session or string_session.strip() == '':
            return False
        
        # Check if session file exists and is recent
        status = self.load_session_status()
        if status.get('created'):
            created_time = datetime.fromisoformat(status['created'])
            # Session is valid for 30 days
            if datetime.now() - created_time < timedelta(days=30):
                return True
        
        return False
    
    async def create_string_session_auto(self):
        """Create string session automatically for Railway deployment"""
        print("🚀 Railway Session Manager - Auto String Session Creation")
        print("=" * 60)
        
        if not API_ID or not API_HASH or not PHONE_NUMBER:
            print("❌ Missing required environment variables:")
            print("   - TELEGRAM_API_ID")
            print("   - TELEGRAM_API_HASH") 
            print("   - TELEGRAM_PHONE")
            print("\n📝 Please set these in Railway Dashboard > Variables")
            return False
        
        try:
            # Create client with unique session name
            session_name = f"railway_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            client = TelegramClient(session_name, API_ID, API_HASH)
            
            print(f"📱 Phone: {PHONE_NUMBER}")
            print(f"🔑 API ID: {API_ID}")
            print(f"🔒 API Hash: {API_HASH[:8]}...{API_HASH[-8:]}")
            print("\n📡 Connecting to Telegram...")
            
            await client.connect()
            
            if not await client.is_user_authorized():
                print("🔑 Sending OTP code...")
                await client.send_code_request(PHONE_NUMBER)
                
                # For Railway, we need to handle this differently
                print("\n" + "=" * 60)
                print("🚨 RAILWAY DEPLOYMENT INSTRUCTIONS")
                print("=" * 60)
                print("1️⃣ Check your Telegram app for the OTP code")
                print("2️⃣ Run this command locally with the code:")
                print(f"   python railway_otp_handler.py YOUR_OTP_CODE")
                print("3️⃣ The script will create and save the string session")
                print("4️⃣ Redeploy to Railway with the updated .env")
                print("=" * 60)
                
                # Save pending status
                self.save_session_status({
                    'status': 'pending_otp',
                    'created': None,
                    'last_check': datetime.now().isoformat(),
                    'session_name': session_name
                })
                
                await client.disconnect()
                return False
                
            else:
                print("✅ Already authorized! Converting to string session...")
                
                # Convert to string session
                string_session = StringSession.save(client.session)
                
                # Save to .env file
                set_key(self.env_path, 'TELEGRAM_STRING_SESSION', string_session)
                load_dotenv(override=True)
                
                # Update status
                self.save_session_status({
                    'status': 'created',
                    'created': datetime.now().isoformat(),
                    'last_check': datetime.now().isoformat(),
                    'session_name': session_name
                })
                
                print(f"✅ String session created and saved to .env!")
                print(f"📅 Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("🎉 Ready for Railway deployment!")
                
                await client.disconnect()
                
                # Clean up temporary files
                temp_files = [f"{session_name}.session", f"{session_name}.session-journal"]
                for file in temp_files:
                    if os.path.exists(file):
                        os.remove(file)
                
                return True
                
        except Exception as e:
            print(f"❌ Error creating session: {e}")
            self.save_session_status({
                'status': 'error',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            })
            return False
    
    async def verify_otp_and_create_session(self, otp_code):
        """Verify OTP and create string session"""
        try:
            status = self.load_session_status()
            if status.get('status') != 'pending_otp':
                print("❌ No pending OTP request found")
                return False
            
            session_name = status.get('session_name')
            client = TelegramClient(session_name, API_ID, API_HASH)
            
            print(f"🔍 Verifying OTP code: {otp_code}")
            await client.connect()
            
            try:
                await client.sign_in(PHONE_NUMBER, otp_code)
                print("✅ OTP verified successfully!")
                
                # Convert to string session
                string_session = StringSession.save(client.session)
                
                # Save to .env file
                set_key(self.env_path, 'TELEGRAM_STRING_SESSION', string_session)
                load_dotenv(override=True)
                
                # Update status
                self.save_session_status({
                    'status': 'created',
                    'created': datetime.now().isoformat(),
                    'last_check': datetime.now().isoformat()
                })
                
                print(f"✅ String session saved to .env!")
                print("🎉 Ready for Railway deployment!")
                
                await client.disconnect()
                
                # Clean up temporary files
                temp_files = [f"{session_name}.session", f"{session_name}.session-journal"]
                for file in temp_files:
                    if os.path.exists(file):
                        os.remove(file)
                
                return True
                
            except Exception as e:
                print(f"❌ Invalid OTP code: {e}")
                await client.disconnect()
                return False
                
        except Exception as e:
            print(f"❌ Error verifying OTP: {e}")
            return False

async def main():
    manager = RailwaySessionManager()
    
    # Check if we already have a valid string session
    if manager.has_valid_string_session():
        print("✅ Valid string session already exists!")
        print("🎉 Ready for Railway deployment!")
        
        status = manager.load_session_status()
        print(f"📅 Created: {status.get('created', 'Unknown')}")
        return
    
    # Try to create automatic session
    success = await manager.create_string_session_auto()
    
    if success:
        print("\n🚀 DEPLOYMENT READY!")
        print("Your .env file now contains TELEGRAM_STRING_SESSION")
        print("You can deploy to Railway now!")
    else:
        print("\n📝 Follow the instructions above to complete setup")

if __name__ == "__main__":
    asyncio.run(main())
