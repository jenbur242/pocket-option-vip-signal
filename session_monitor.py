#!/usr/bin/env python3
"""
Session Monitor Service
Continuously monitors Telegram session expiration and handles automatic renewal
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
STRING_SESSION = os.getenv('TELEGRAM_STRING_SESSION')

class SessionMonitor:
    def __init__(self):
        self.status_file = 'session_monitor_status.json'
        self.check_interval = 300  # 5 minutes
        self.session_expiry_hours = 24  # 24 hours
        
    def load_monitor_status(self):
        """Load monitor status"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {
            'last_check': None,
            'session_status': 'unknown',
            'expiry_time': None,
            'renewal_requested': False
        }
    
    def save_monitor_status(self, status_data):
        """Save monitor status"""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
        except Exception as e:
            print(f"Failed to save monitor status: {e}")
    
    async def check_string_session_validity(self):
        """Check if string session is still valid"""
        if not STRING_SESSION:
            return {'valid': False, 'reason': 'no_string_session'}
        
        try:
            # Create temporary client to test session
            client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
            
            await client.connect()
            
            if await client.is_user_authorized():
                # Get session info
                me = await client.get_me()
                await client.disconnect()
                
                return {
                    'valid': True,
                    'user_id': me.id,
                    'username': me.username,
                    'phone': me.phone,
                    'reason': 'valid'
                }
            else:
                await client.disconnect()
                return {'valid': False, 'reason': 'unauthorized'}
                
        except Exception as e:
            return {'valid': False, 'reason': str(e)}
    
    def calculate_session_expiry(self):
        """Calculate when session should expire"""
        status = self.load_monitor_status()
        
        if status.get('session_created'):
            created_time = datetime.fromisoformat(status['session_created'])
            expiry_time = created_time + timedelta(hours=self.session_expiry_hours)
            return expiry_time
        
        return None
    
    async def monitor_session(self):
        """Main monitoring loop"""
        print("🔍 Session Monitor Started - Checking every 5 minutes")
        print(f"⏰ Session expiry: {self.session_expiry_hours} hours")
        
        while True:
            try:
                current_time = datetime.now()
                status = self.load_monitor_status()
                
                # Check session validity
                session_check = await self.check_string_session_validity()
                
                if session_check['valid']:
                    print(f"✅ Session valid - User: @{session_check.get('username', 'Unknown')}")
                    
                    # Update status
                    status.update({
                        'last_check': current_time.isoformat(),
                        'session_status': 'valid',
                        'user_info': session_check,
                        'renewal_requested': False
                    })
                    
                else:
                    print(f"❌ Session invalid - Reason: {session_check['reason']}")
                    
                    # Calculate expiry time
                    expiry_time = self.calculate_session_expiry()
                    
                    # Update status with expiration
                    status.update({
                        'last_check': current_time.isoformat(),
                        'session_status': 'expired',
                        'expiry_time': expiry_time.isoformat() if expiry_time else None,
                        'renewal_requested': True,
                        'reason': session_check['reason']
                    })
                    
                    # Create renewal request file for frontend
                    await self.create_renewal_request(session_check)
                    
                    print("🔄 Session renewal requested - Frontend will show OTP prompt")
                
                self.save_monitor_status(status)
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def create_renewal_request(self, session_check):
        """Create renewal request for frontend"""
        renewal_data = {
            'requested_at': datetime.now().isoformat(),
            'reason': session_check['reason'],
            'session_status': 'expired',
            'requires_otp': True,
            'phone': PHONE_NUMBER,
            'api_id': API_ID
        }
        
        try:
            with open('session_renewal_request.json', 'w') as f:
                json.dump(renewal_data, f, indent=2)
            print("📝 Renewal request created for frontend")
        except Exception as e:
            print(f"Failed to create renewal request: {e}")

async def start_session_monitor():
    """Start the session monitoring service"""
    monitor = SessionMonitor()
    await monitor.monitor_session()

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 TELEGRAM SESSION MONITOR")
    print("=" * 60)
    asyncio.run(start_session_monitor())
