#!/usr/bin/env python3
"""
Automatic Railway Session Creator
Creates Telegram string sessions automatically on Railway deployment
"""

import os
import asyncio
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv, set_key
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RailwayAutoSession:
    def __init__(self):
        self.env_path = '/app/.env'  # Railway persistent storage
        self.session_file = '/app/railway_session_status.json'
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')
        
    def load_session_status(self):
        """Load session status from Railway storage"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {'created': None, 'status': 'none', 'attempts': 0}
    
    def save_session_status(self, status_data):
        """Save session status to Railway storage"""
        try:
            with open(self.session_file, 'w') as f:
                json.dump(status_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save session status: {e}")
    
    def has_valid_session(self):
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
    
    async def test_existing_session(self):
        """Test if existing string session is valid"""
        string_session = os.getenv('TELEGRAM_STRING_SESSION')
        if not string_session:
            return False
        
        try:
            client = TelegramClient(StringSession(string_session), self.api_id, self.api_hash)
            await client.connect()
            
            if await client.is_user_authorized():
                me = await client.get_me()
                await client.disconnect()
                logger.info(f"✅ Existing session valid - User: @{me.username}")
                return True
            else:
                await client.disconnect()
                logger.warning("⚠️ Existing session invalid")
                return False
                
        except Exception as e:
            logger.error(f"❌ Session test failed: {e}")
            return False
    
    async def create_auto_session(self):
        """Create session automatically using Railway's unique identifier"""
        logger.info("🚀 Starting automatic session creation for Railway")
        
        if not all([self.api_id, self.api_hash, self.phone]):
            logger.error("❌ Missing Telegram credentials in environment")
            return False
        
        # Check if we already have a valid session
        if await self.test_existing_session():
            logger.info("✅ Valid session already exists")
            return True
        
        # Create unique session name using Railway's unique identifier
        import socket
        hostname = socket.gethostname()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_name = f"railway_auto_{hostname}_{timestamp}"
        
        logger.info(f"📱 Creating auto-session: {session_name}")
        logger.info(f"📞 Phone: {self.phone}")
        
        try:
            # Create client and send OTP
            client = TelegramClient(session_name, self.api_id, self.api_hash)
            
            await client.connect()
            logger.info("🔑 Sending OTP to Telegram...")
            
            # For Railway, we need to handle OTP differently
            # We'll create a renewal request that the frontend can handle
            renewal_request = {
                'auto_session_requested': True,
                'session_name': session_name,
                'phone': self.phone,
                'api_id': self.api_id,
                'requested_at': datetime.now().isoformat(),
                'status': 'awaiting_otp',
                'hostname': hostname,
                'railway_deploy': True
            }
            
            self.save_session_status(renewal_request)
            
            # Send OTP code
            await client.send_code_request(self.phone)
            
            logger.info("📨 OTP sent - waiting for verification...")
            logger.info("💡 Frontend will show OTP input modal")
            logger.info("💡 Or use Railway logs to get OTP code")
            
            await client.disconnect()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Auto session creation failed: {e}")
            
            # Update status with error
            error_status = {
                'auto_session_requested': True,
                'error': str(e),
                'requested_at': datetime.now().isoformat(),
                'status': 'failed'
            }
            self.save_session_status(error_status)
            
            return False
    
    async def complete_auto_session(self, otp_code):
        """Complete automatic session with OTP"""
        try:
            status = self.load_session_status()
            session_name = status.get('session_name')
            
            if not session_name:
                logger.error("❌ No pending auto-session found")
                return False
            
            logger.info(f"🔍 Completing auto-session with OTP: {otp_code}")
            
            client = TelegramClient(session_name, self.api_id, self.api_hash)
            await client.connect()
            await client.sign_in(self.phone, otp_code)
            
            # Convert to string session
            string_session = StringSession.save(client.session)
            
            # Save to .env
            set_key(self.env_path, 'TELEGRAM_STRING_SESSION', string_session)
            load_dotenv(override=True)
            
            # Update status
            success_status = {
                'auto_session_requested': True,
                'completed_at': datetime.now().isoformat(),
                'status': 'completed',
                'string_session_length': len(string_session),
                'hostname': status.get('hostname'),
                'railway_deploy': True
            }
            
            self.save_session_status(success_status)
            
            logger.info("✅ Auto-session completed and saved to .env")
            logger.info("🚀 Railway deployment ready!")
            
            await client.disconnect()
            
            # Clean up temporary files
            temp_files = [f"{session_name}.session", f"{session_name}.session-journal"]
            for file in temp_files:
                if os.path.exists(file):
                    os.remove(file)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Auto-session completion failed: {e}")
            return False

async def main():
    """Main function for Railway automatic session creation"""
    print("=" * 60)
    print("🤖 RAILWAY AUTO SESSION CREATOR")
    print("=" * 60)
    
    auto_session = RailwayAutoSession()
    
    # Check if we need to create a session
    if auto_session.has_valid_session():
        print("✅ Valid session already exists - Railway ready!")
        print("🚀 Bot can start automatically")
        return
    
    print("🔄 No valid session found - creating auto-session...")
    
    success = await auto_session.create_auto_session()
    
    if success:
        print("\n" + "=" * 60)
        print("📨 OTP SENT SUCCESSFULLY")
        print("=" * 60)
        print("🔍 NEXT STEPS:")
        print("1️⃣ Check Railway logs for OTP code")
        print("2️⃣ Call this API endpoint:")
        print("   POST /api/sessions/complete-auto")
        print("   Body: {\"otp_code\": \"YOUR_CODE\"}")
        print("3️⃣ Session will be created automatically")
        print("4️⃣ Bot will restart with new session")
        print("=" * 60)
        
        # Create API endpoint for completion
        await create_completion_endpoint(auto_session)
        
    else:
        print("❌ Auto-session creation failed")
        print("💡 Check Railway logs for error details")

async def create_completion_endpoint(auto_session):
    """Create Flask endpoint for completing auto-session"""
    endpoint_code = f'''
@app.route('/api/sessions/complete-auto', methods=['POST'])
def complete_auto_session():
    """Complete automatic Railway session"""
    try:
        data = request.get_json()
        otp_code = data.get('otp_code')
        
        if not otp_code:
            return jsonify({{'error': 'OTP code required'}), 400
        
        # Complete the session
        success = await auto_session.complete_auto_session(otp_code)
        
        if success:
            return jsonify({{
                'success': True,
                'message': 'Auto-session completed! Railway deployment ready.'
            }})
        else:
            return jsonify({{'error': 'Failed to complete auto-session'}), 500
            
    except Exception as e:
        return jsonify({{'error': str(e)}), 500
'''
    
    # Save endpoint to file
    with open('/app/auto_session_endpoint.py', 'w') as f:
        f.write(endpoint_code)
    
    print("📝 Auto-session completion endpoint created")
    print("💡 Add this to your api_server.py")

if __name__ == "__main__":
    asyncio.run(main())
