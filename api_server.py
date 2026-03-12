#!/usr/bin/env python3
"""
Flask API Server for Pocket Option Trading Bot
Provides endpoints for frontend to manage SSID, start trading, and view results
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import session cleanup system
from session_cleanup import register_session, update_session_access, cleanup_expired_sessions, get_session_status

# Import Telegram components
from telethon.sessions import StringSession

# Import trading modules
from telegram.main import (
    main as telegram_main,
    past_trades,
    global_martingale_step,
    get_trade_amount,
    get_multiplier,
    get_is_demo,
    get_initial_balance,
    update_trading_config,
    dynamic_trade_amount,
    dynamic_multiplier,
    dynamic_is_demo,
    dynamic_initial_balance
)

# upcoming_trades removed from simplified main.py
upcoming_trades = []

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Configure logging
import logging
logger = logging.getLogger(__name__)

# Global state
trading_active = False
trading_thread = None
trade_results = []  # Store all trade results
temp_phone_code_hash = None  # Temporary storage for OTP verification
active_client = None  # Store active PocketOption client
client_balance = {'demo': 0, 'real': 0}  # Cache balance
data_mode = 'real'  # Global data mode: 'real' or 'dummy'
dummy_data_cache = {}  # Cache for dummy data

# Persistent client management
class PersistentClientManager:
    """Manages a single persistent PocketOption client connection"""
    def __init__(self):
        self.demo_client = None
        self.real_client = None
        self.demo_connected = False
        self.real_connected = False
        self.last_balance_fetch = None
        self.balance_cache = {'demo': 0, 'real': 0, 'currency': 'USD'}
        self.connection_lock = threading.Lock()
        self.demo_ssid = None
        self.real_ssid = None
        self.current_mode = None  # Track current trading mode
        
    def get_ssid_for_mode(self, is_demo: bool):
        """Get appropriate SSID based on mode"""
        from telegram.main import SSID_DEMO, SSID_REAL
        
        if is_demo:
            return SSID_DEMO
        else:
            return SSID_REAL
        
    async def get_client_for_mode(self, is_demo: bool):
        """Get client based on trading mode (demo or real)"""
        ssid = self.get_ssid_for_mode(is_demo)
        if is_demo:
            return await self.get_demo_client(ssid)
        else:
            return await self.get_real_client(ssid)
        
    async def get_demo_client(self, ssid: str):
        """Get or create demo client"""
        from pocketoptionapi_async import AsyncPocketOptionClient
        
        # Check if SSID changed
        if self.demo_ssid != ssid:
            if self.demo_client:
                try:
                    await self.demo_client.disconnect()
                    await asyncio.sleep(0.2)
                except:
                    pass
            self.demo_client = None
            self.demo_connected = False
            self.demo_ssid = ssid
        
        # Return existing client if connected
        if self.demo_client and self.demo_connected:
            try:
                # Test connection
                await asyncio.wait_for(self.demo_client.get_balance(), timeout=2.0)
                print("SUCCESS: Reusing existing demo client connection")
                return self.demo_client
            except:
                print("WARNING: Demo client connection lost, reconnecting...")
                self.demo_connected = False
        
        # Create new client
        print("CONNECT: Creating new demo client connection...")
        self.demo_client = AsyncPocketOptionClient(ssid=ssid, is_demo=True)
        await asyncio.wait_for(self.demo_client.connect(), timeout=20.0)
        self.demo_connected = True
        print("SUCCESS: Demo client connected")
        return self.demo_client
    
    async def get_real_client(self, ssid: str):
        """Get or create real client"""
        from pocketoptionapi_async import AsyncPocketOptionClient
        
        # Check if SSID changed
        if self.real_ssid != ssid:
            if self.real_client:
                try:
                    await self.real_client.disconnect()
                    await asyncio.sleep(0.2)
                except:
                    pass
            self.real_client = None
            self.real_connected = False
            self.real_ssid = ssid
        
        # Return existing client if connected
        if self.real_client and self.real_connected:
            try:
                # Test connection
                await asyncio.wait_for(self.real_client.get_balance(), timeout=2.0)
                print("SUCCESS: Reusing existing real client connection")
                return self.real_client
            except:
                print("WARNING: Real client connection lost, reconnecting...")
                self.real_connected = False
        
        # Create new client
        print("CONNECT: Creating new real client connection...")
        self.real_client = AsyncPocketOptionClient(ssid=ssid, is_demo=False)
        await asyncio.wait_for(self.real_client.connect(), timeout=20.0)
        self.real_connected = True
        print("SUCCESS: Real client connected")
        return self.real_client
    
    async def disconnect_all(self):
        """Disconnect all clients"""
        if self.demo_client:
            try:
                await self.demo_client.disconnect()
                await asyncio.sleep(0.2)
            except:
                pass
            self.demo_client = None
            self.demo_connected = False
        
        if self.real_client:
            try:
                await self.real_client.disconnect()
                await asyncio.sleep(0.2)
            except:
                pass
            self.real_client = None
            self.real_connected = False
        
        print("🔌 All clients disconnected")
    
    def get_current_mode(self):
        """Get current trading mode from .env"""
        is_demo = os.getenv('IS_DEMO', 'True').lower() == 'true'
        return is_demo

# Global persistent client manager
persistent_client_manager = PersistentClientManager()

@app.route('/', methods=['GET'])
def index():
    """Serve the frontend HTML"""
    try:
        return send_file('frontend.html')
    except Exception as e:
        return jsonify({
            'error': 'Frontend file not found',
            'message': str(e),
            'api_info': {
                'message': 'Pocket Option Trading API',
                'version': '1.0.0',
                'endpoints': {
                    'health': 'GET /api/health',
                    'ssid': 'POST /api/ssid',
                    'telegram': 'POST /api/telegram/otp',
                    'start_trading': 'POST /api/trading/start',
                    'stop_trading': 'POST /api/trading/stop',
                    'status': 'GET /api/trading/status',
                    'results': 'GET /api/trades/results',
                    'upcoming': 'GET /api/trades/upcoming',
                    'analysis': 'GET /api/trades/analysis'
                }
            }
        }), 404

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    global persistent_client_manager
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'connections': {
            'demo': persistent_client_manager.demo_connected,
            'real': persistent_client_manager.real_connected
        }
    })

@app.route('/api/connection/status', methods=['GET'])
def get_connection_status():
    """Get persistent connection status"""
    global persistent_client_manager
    return jsonify({
        'demo_connected': persistent_client_manager.demo_connected,
        'real_connected': persistent_client_manager.real_connected,
        'last_balance_fetch': persistent_client_manager.last_balance_fetch.isoformat() if persistent_client_manager.last_balance_fetch else None,
        'cached_balance': persistent_client_manager.balance_cache
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """
    Get current configuration from .env file
    Returns SSID status, Telegram config, and trading config (without sensitive values)
    """
    try:
        ssid_demo = os.getenv('SSID_DEMO') or os.getenv('SSID')
        ssid_real = os.getenv('SSID_REAL')
        telegram_api_id = os.getenv('TELEGRAM_API_ID')
        telegram_api_hash = os.getenv('TELEGRAM_API_HASH')
        telegram_phone = os.getenv('TELEGRAM_PHONE')
        telegram_channel = os.getenv('TELEGRAM_CHANNEL', 'testpob1234')
        
        # Get trading configuration from .env
        trade_amount = float(os.getenv('TRADE_AMOUNT', '1.0'))
        is_demo = os.getenv('IS_DEMO', 'True').lower() == 'true'
        multiplier = float(os.getenv('MULTIPLIER', '2.5'))
        martingale_step = int(os.getenv('MARTINGALE_STEP', '0'))
        
        # Mask SSIDs for display (show first 20 and last 10 characters)
        def mask_ssid(ssid):
            if ssid and len(ssid) > 30:
                return ssid[:20] + '...' + ssid[-10:]
            elif ssid:
                return ssid[:10] + '...'
            return None
        
        masked_ssid_demo = mask_ssid(ssid_demo)
        masked_ssid_real = mask_ssid(ssid_real)
        
        return jsonify({
            'ssid_demo_configured': bool(ssid_demo),
            'ssid_real_configured': bool(ssid_real),
            'ssid_demo_preview': masked_ssid_demo,
            'ssid_real_preview': masked_ssid_real,
            # Legacy fields for backward compatibility
            'ssid_configured': bool(ssid_demo),
            'ssid_preview': masked_ssid_demo,
            'telegram_configured': bool(telegram_api_id and telegram_api_hash and telegram_phone),
            'telegram': {
                'api_id': telegram_api_id if telegram_api_id else None,
                'api_hash': '***' + telegram_api_hash[-4:] if telegram_api_hash and len(telegram_api_hash) > 4 else None,
                'phone': telegram_phone if telegram_phone else None,
                'channel': telegram_channel
            },
            'trading': {
                'trade_amount': trade_amount,
                'is_demo': is_demo,
                'multiplier': multiplier,
                'martingale_step': martingale_step
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ssid', methods=['POST'])
def set_ssid():
    """
    Set SSIDs for trading (both Demo and Real)
    Body: { "ssid_demo": "42[\"auth\",{...}]", "ssid_real": "42[\"auth\",{...}]" }
    """
    try:
        return jsonify({
            'success': True,
            'message': 'SSIDs saved successfully',
            'demo_configured': bool(ssid_demo),
            'real_configured': bool(ssid_real)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/monitor-status', methods=['GET'])
def get_session_monitor_status():
    """Get current session monitoring status"""
    try:
        # Check for renewal request
        renewal_request = None
        if os.path.exists('session_renewal_request.json'):
            with open('session_renewal_request.json', 'r') as f:
                renewal_request = json.load(f)
        
        # Check monitor status
        monitor_status = None
        if os.path.exists('session_monitor_status.json'):
            with open('session_monitor_status.json', 'r') as f:
                monitor_status = json.load(f)
        
        return jsonify({
            'success': True,
            'renewal_request': renewal_request,
            'monitor_status': monitor_status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/renew', methods=['POST'])
def request_session_renewal():
    """Request session renewal via OTP"""
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action == 'start_renewal':
            # Check if renewal is already requested
            if os.path.exists('session_renewal_request.json'):
                with open('session_renewal_request.json', 'r') as f:
                    existing_request = json.load(f)
                
                # Check if request is recent (within 5 minutes)
                requested_at = datetime.fromisoformat(existing_request['requested_at'])
                if datetime.now() - requested_at < timedelta(minutes=5):
                    return jsonify({
                        'success': False,
                        'message': 'Renewal already requested. Please wait for OTP.'
                    })
            
            # Create new renewal request
            renewal_request = {
                'requested_at': datetime.now().isoformat(),
                'action': 'send_otp',
                'session_status': 'expired',
                'requires_otp': True,
                'phone': os.getenv('TELEGRAM_PHONE'),
                'api_id': os.getenv('TELEGRAM_API_ID')
            }
            
            with open('session_renewal_request.json', 'w') as f:
                json.dump(renewal_request, f, indent=2)
            
            return jsonify({
                'success': True,
                'message': 'Session renewal requested. OTP will be sent to your phone.',
                'renewal_request': renewal_request
            })
        
        elif action == 'complete_renewal':
            # Complete renewal with OTP
            otp_code = data.get('otp_code')
            if not otp_code:
                return jsonify({'error': 'OTP code is required'}), 400
            
            # Process OTP verification
            from telegram.main import API_ID, API_HASH, PHONE_NUMBER
            from telethon.sync import TelegramClient
            from telethon.sessions import StringSession
            
            try:
                # Create temporary session for OTP verification
                async def complete_renewal():
                    client = TelegramClient('renewal_session', API_ID, API_HASH)
                    await client.connect()
                    await client.sign_in(PHONE_NUMBER, otp_code)
                    
                    # Convert to string session
                    string_session = StringSession.save(client.session)
                    
                    # Save to .env
                    env_path = os.path.join(os.path.dirname(__file__), '.env')
                    set_key(env_path, 'TELEGRAM_STRING_SESSION', string_session)
                    load_dotenv(override=True)
                    
                    # Clean up
                    await client.disconnect()
                    
                    # Remove renewal request
                    if os.path.exists('session_renewal_request.json'):
                        os.remove('session_renewal_request.json')
                    
                    # Clean up temporary files
                    temp_files = ['renewal_session.session', 'renewal_session.session-journal']
                    for file in temp_files:
                        if os.path.exists(file):
                            os.remove(file)
                    
                    return string_session
                
                # Run async function
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                string_session = loop.run_until_complete(complete_renewal())
                loop.close()
                
                return jsonify({
                    'success': True,
                    'message': 'Session renewed successfully! Bot will reconnect automatically.',
                    'string_session_created': True
                })
                
            except Exception as e:
                return jsonify({'error': f'OTP verification failed: {str(e)}'}), 500
        
        else:
            return jsonify({'error': 'Invalid action'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/complete-auto', methods=['POST'])
def complete_auto_session():
    """Complete automatic Railway session"""
    try:
        data = request.get_json()
        otp_code = data.get('otp_code')
        
        if not otp_code:
            return jsonify({'error': 'OTP code required'}), 400
        
        # Load auto-session status
        status = None
        if os.path.exists('railway_session_status.json'):
            with open('railway_session_status.json', 'r') as f:
                status = json.load(f)
        
        if not status or not status.get('session_name'):
            return jsonify({'error': 'No pending auto-session found'}), 400
        
        session_name = status.get('session_name')
        phone = status.get('phone')
        api_id = status.get('api_id')
        api_hash = status.get('api_hash')
        
        logger.info(f"🔍 Completing auto-session with OTP: {otp_code}")
        
        try:
            # Complete the session
            async def complete_auto_session():
                client = TelegramClient(session_name, api_id, api_hash)
                await client.connect()
                await client.sign_in(phone, otp_code)
                
                # Convert to string session
                string_session = StringSession.save(client.session)
                
                # Save to .env
                env_path = os.path.join(os.path.dirname(__file__), '.env')
                set_key(env_path, 'TELEGRAM_STRING_SESSION', string_session)
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
                
                with open('railway_session_status.json', 'w') as f:
                    json.dump(success_status, f, indent=2)
                
                logger.info("SUCCESS: Auto-session completed and saved to .env")
                logger.info("RAILWAY: Railway deployment ready!")
                
                await client.disconnect()
                
                # Clean up temporary files
                temp_files = [f"{session_name}.session", f"{session_name}.session-journal"]
                for file in temp_files:
                    if os.path.exists(file):
                        os.remove(file)
                
                return string_session
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            string_session = loop.run_until_complete(complete_auto_session())
            loop.close()
            
            return jsonify({
                'success': True,
                'message': 'Auto-session completed! Railway deployment ready.',
                'string_session_created': True
            })
            
        except Exception as e:
            logger.error(f"ERROR: Auto-session completion failed: {e}")
            return jsonify({'error': f'Failed to complete auto-session: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/clear-renewal', methods=['POST'])
def clear_renewal_request():
    """Clear session renewal request"""
    try:
        if os.path.exists('session_renewal_request.json'):
            os.remove('session_renewal_request.json')
        
        return jsonify({
            'success': True,
            'message': 'Renewal request cleared'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/telegram/check-session', methods=['GET'])
def check_telegram_session():
    """
    Check if Telegram session exists (file or string session)
    """
    try:
        # Check if session file exists
        session_file = 'po_vip_testing.session'
        session_file_exists = os.path.exists(session_file)
        
        # Check if string session is set in main.py
        from telegram.main import STRING_SESSION, API_ID, API_HASH, PHONE_NUMBER
        session_env_exists = bool(STRING_SESSION)
        
        # Session exists if either file exists or string session is set
        session_exists = session_file_exists or session_env_exists
        
        # Determine session type for debugging
        session_type = None
        if session_file_exists:
            session_type = 'file'
        elif session_env_exists:
            session_type = 'string'
        
        # Check if credentials are configured (using hardcoded values)
        credentials_configured = bool(API_ID and API_HASH and PHONE_NUMBER)
        
        return jsonify({
            'success': True,
            'session_exists': session_exists,
            'session_type': session_type,
            'string_session_exists': session_env_exists,
            'session_file_exists': session_file_exists,
            'credentials_configured': credentials_configured,
            'phone': PHONE_NUMBER,
            'api_id': API_ID,
            'api_hash': API_HASH[-4:] if API_HASH else None  # Only show last 4 chars
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/telegram/send-code', methods=['POST'])
def send_telegram_code():
    """
    Send OTP code to phone number
    """
    try:
        # Use hardcoded credentials from main.py
        from telegram.main import API_ID, API_HASH, PHONE_NUMBER
        
        if not all([API_ID, API_HASH, PHONE_NUMBER]):
            return jsonify({'error': 'Telegram credentials not configured'}), 400
        
        # Import Telethon
        from telethon.sync import TelegramClient
        
        # Create client and send code
        client = TelegramClient('po_vip_testing', API_ID, API_HASH)
        
        async def send_code():
            await client.connect()
            if not await client.is_user_authorized():
                result = await client.send_code_request(PHONE_NUMBER)
                await client.disconnect()
                return result.phone_code_hash
            else:
                await client.disconnect()
                return None
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        phone_code_hash = loop.run_until_complete(send_code())
        loop.close()
        
        if phone_code_hash:
            # Store phone_code_hash temporarily (in production, use Redis or database)
            global temp_phone_code_hash
            temp_phone_code_hash = phone_code_hash
            
            return jsonify({
                'success': True,
                'message': f'OTP code sent to {phone}',
                'phone': phone
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Already authorized',
                'session_exists': True
            })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/status', methods=['GET'])
def get_sessions_status():
    """Get session status and cleanup information"""
    try:
        from session_cleanup import get_session_stats, get_all_sessions
        
        # Get basic session status
        status = get_session_status()
        
        # Get detailed session stats
        stats = get_session_stats()
        all_sessions = get_all_sessions()
        
        return jsonify({
            'success': True,
            'session_status': status,
            'stats': stats,
            'active_sessions': all_sessions,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/cleanup', methods=['POST'])
def manual_session_cleanup():
    """Manual session cleanup"""
    try:
        result = cleanup_expired_sessions()
        return jsonify({
            'success': True,
            'message': f'Cleanup completed. Deleted {result["deleted_count"]} files.',
            'result': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/telegram/verify-otp', methods=['POST'])
def verify_telegram_otp():
    """
    Verify OTP code and create session
    Body: { "code": "12345" }
    """
    try:
        data = request.get_json()
        code = data.get('code')
        
        if not code:
            return jsonify({'error': 'OTP code is required'}), 400
        
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        phone = os.getenv('TELEGRAM_PHONE')
        
        if not all([api_id, api_hash, phone]):
            return jsonify({'error': 'Telegram credentials not configured'}), 400
        
        # Get stored phone_code_hash
        global temp_phone_code_hash
        if not temp_phone_code_hash:
            return jsonify({'error': 'Please request OTP code first'}), 400
        
        # Import Telethon
        from telethon.sync import TelegramClient
        
        # Create client and verify code
        client = TelegramClient('po_vip_testing', api_id, api_hash)
        
        async def verify_code():
            await client.connect()
            try:
                await client.sign_in(phone, code, phone_code_hash=temp_phone_code_hash)
                await client.disconnect()
                return True
            except Exception as e:
                await client.disconnect()
                raise e
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(verify_code())
        loop.close()
        
        # Clear temp hash
        temp_phone_code_hash = None
        
        # Get the string session from the created session file
        session_file = 'po_vip_testing.session'
        string_session = None
        
        if os.path.exists(session_file):
            try:
                # Read the session file and convert to string session
                from telethon.sync import TelegramClient
                temp_client = TelegramClient(session_file, api_id, api_hash)
                temp_client.connect()
                if temp_client.is_user_authorized():
                    string_session = StringSession.save(temp_client.session)
                    temp_client.disconnect()
                    
                    # Save string session to .env file
                    env_path = os.path.join(os.path.dirname(__file__), '.env')
                    set_key(env_path, 'TELEGRAM_STRING_SESSION', string_session)
                    load_dotenv(override=True)
                    
                    # Register session with cleanup system
                    register_session(session_file, phone)
                    
                    # Delete the session file since we now have string session
                    os.remove(session_file)
                    if os.path.exists(session_file + '-journal'):
                        os.remove(session_file + '-journal')
                    
                    log_message("SUCCESS: String session saved to .env file")
                    
                else:
                    temp_client.disconnect()
                    
            except Exception as e:
                print(f"Error converting session to string: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Telegram session created successfully!',
            'session_exists': True,
            'session_registered': True,
            'string_session_created': bool(string_session)
        })
    
    except Exception as e:
        return jsonify({'error': f'OTP verification failed: {str(e)}'}), 500

@app.route('/api/telegram/delete-session', methods=['POST'])
def delete_telegram_session():
    """
    Delete Telegram session files and string session
    """
    try:
        session_files = [
            'po_vip_testing.session',
            'po_vip_testing.session-journal'
        ]
        
        deleted_files = []
        for session_file in session_files:
            if os.path.exists(session_file):
                os.remove(session_file)
                deleted_files.append(session_file)
        
        # Also remove string session from .env
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        set_key(env_path, 'TELEGRAM_STRING_SESSION', '')
        load_dotenv(override=True)
        
        if deleted_files or os.getenv('TELEGRAM_STRING_SESSION') == '':
            return jsonify({
                'success': True,
                'message': f'Deleted {len(deleted_files)} session file(s) and cleared string session',
                'deleted_files': deleted_files,
                'string_session_cleared': True
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No session files found to delete',
                'deleted_files': deleted_files,
                'string_session_cleared': True
            })
    
    except Exception as e:
        return jsonify({'error': f'Failed to delete session: {str(e)}'}), 500

@app.route('/api/clear-all-sessions', methods=['POST'])
def clear_all_sessions():
    """
    Clear all session files, database locks, and temporary files
    """
    try:
        files_to_delete = [
            # Telegram session files
            'po_vip_testing.session',
            'po_vip_testing.session-journal',
            
            # Any other session files (pattern matching)
            'session_*.session',
            'session_*.session-journal',
            
            # Database lock files
            '*.db-shm',
            '*.db-wal',
            '*.db-journal',
            
            # Temporary files
            '*.tmp',
            '*.lock'
        ]
        
        deleted_files = []
        
        # Delete specific files
        for pattern in files_to_delete:
            if '*' in pattern:
                # Handle wildcard patterns
                import glob
                matching_files = glob.glob(pattern)
                for file_path in matching_files:
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                            deleted_files.append(file_path)
                        except Exception as e:
                            print(f"Could not delete {file_path}: {e}")
            else:
                # Handle specific files
                if os.path.exists(pattern):
                    try:
                        os.remove(pattern)
                        deleted_files.append(pattern)
                    except Exception as e:
                        print(f"Could not delete {pattern}: {e}")
        
        if deleted_files:
            return jsonify({
                'success': True,
                'message': f'Successfully cleared {len(deleted_files)} file(s)',
                'deleted_files': deleted_files
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No session or lock files found to delete',
                'deleted_files': []
            })
    
    except Exception as e:
        return jsonify({'error': f'Failed to clear sessions: {str(e)}'}), 500

@app.route('/api/telegram/session', methods=['POST'])
def set_telegram_session():
    """
    Set Telegram string session from browser
    Body: { "string_session": "..." }
    """
    try:
        data = request.get_json()
        string_session = data.get('string_session')
        
        if not string_session:
            return jsonify({'error': 'No string session provided'}), 400
        
        # Save to .env file
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        set_key(env_path, 'TELEGRAM_STRING_SESSION', string_session)
        load_dotenv(override=True)
        
        logger.info("Telegram string session saved from browser")
        
        return jsonify({
            'success': True,
            'message': 'Session saved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error saving session: {e}")
        return jsonify({'error': f'Failed to save session: {str(e)}'}), 500

@app.route('/api/telegram/otp', methods=['POST'])
def send_otp():
    """
    Handle Telegram OTP if needed
    Body: { "phone": "+1234567890", "api_id": "...", "api_hash": "..." }
    """
    try:
        data = request.get_json()
        phone = data.get('phone')
        api_id = data.get('api_id')
        api_hash = data.get('api_hash')
        
        if not all([phone, api_id, api_hash]):
            return jsonify({'error': 'Phone, API ID, and API Hash are required'}), 400
        
        # Save to .env
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        set_key(env_path, 'TELEGRAM_PHONE', phone)
        set_key(env_path, 'TELEGRAM_API_ID', api_id)
        set_key(env_path, 'TELEGRAM_API_HASH', api_hash)
        
        load_dotenv(override=True)
        
        return jsonify({
            'success': True,
            'message': 'Telegram credentials saved. OTP will be sent when trading starts.'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/csv/list', methods=['GET'])
def list_csv_files():
    """
    List all CSV files in trade_results folder
    """
    try:
        csv_folder = 'trade_results'
        if not os.path.exists(csv_folder):
            return jsonify({'files': []})
        
        files = []
        for filename in os.listdir(csv_folder):
            if filename.endswith('.csv'):
                filepath = os.path.join(csv_folder, filename)
                file_stats = os.stat(filepath)
                
                files.append({
                    'filename': filename,
                    'date': filename.replace('trades_', '').replace('.csv', ''),
                    'size': file_stats.st_size,
                    'modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                    'path': filepath
                })
        
        # Sort by date descending
        files.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify({'files': files, 'total': len(files)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/csv/read/<filename>', methods=['GET'])
def read_csv_file(filename):
    """
    Read specific CSV file and return data
    """
    try:
        import csv
        
        csv_folder = 'trade_results'
        filepath = os.path.join(csv_folder, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        trades = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                trades.append(row)
        
        # Calculate statistics
        total_trades = len(trades)
        wins = sum(1 for t in trades if t.get('result') == 'win')
        losses = sum(1 for t in trades if t.get('result') == 'loss')
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        total_profit = sum(float(t.get('profit_loss', 0)) for t in trades if t.get('profit_loss'))
        
        return jsonify({
            'filename': filename,
            'trades': trades,
            'statistics': {
                'total_trades': total_trades,
                'wins': wins,
                'losses': losses,
                'win_rate': round(win_rate, 2),
                'total_profit': round(total_profit, 2)
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/csv/download/<filename>', methods=['GET'])
def download_csv_file(filename):
    """
    Download CSV file
    """
    try:
        csv_folder = 'trade_results'
        filepath = os.path.join(csv_folder, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test/telegram', methods=['GET'])
def test_telegram_connection():
    """
    Test Telegram connection and channel access
    """
    try:
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        phone = os.getenv('TELEGRAM_PHONE')
        channel = os.getenv('TELEGRAM_CHANNEL', 'testpob1234')
        string_session = os.getenv('TELEGRAM_STRING_SESSION')
        
        if not all([api_id, api_hash, phone]):
            return jsonify({'error': 'Telegram credentials not configured'}), 400
        
        from telethon.sync import TelegramClient
        from telethon.sessions import StringSession
        
        async def test_connection():
            # Use string session if available, otherwise use file session
            if string_session:
                client = TelegramClient(StringSession(string_session), api_id, api_hash)
                session_type = 'string'
            else:
                client = TelegramClient('po_vip_testing', api_id, api_hash)
                session_type = 'file'
            
            await client.connect()
            
            if not await client.is_user_authorized():
                await client.disconnect()
                return {'error': 'Not authorized. Please create session file first.'}
            
            try:
                # Get channel entity
                channel_entity = await client.get_entity(channel)
                
                # Get recent messages
                messages = await client.get_messages(channel_entity, limit=5)
                
                message_list = []
                for msg in messages:
                    if msg.message:
                        message_list.append({
                            'id': msg.id,
                            'date': msg.date.isoformat(),
                            'text': msg.message[:100] + '...' if len(msg.message) > 100 else msg.message
                        })
                
                await client.disconnect()
                
                return {
                    'success': True,
                    'channel': channel_entity.title,
                    'channel_id': channel_entity.id,
                    'recent_messages': message_list,
                    'message': f'Successfully connected to {channel_entity.title}',
                    'session_type': session_type
                }
                
            except Exception as e:
                await client.disconnect()
                return {'error': f'Failed to access channel: {str(e)}'}
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(test_connection())
        loop.close()
        
        if 'error' in result:
            return jsonify(result), 400
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Start/Stop endpoints removed - bot runs continuously

@app.route('/api/trading/clear-pending', methods=['POST'])
def clear_pending_trades():
    """Clear all pending trades (useful for stuck trades)"""
    global past_trades
    
    try:
        pending_before = sum(1 for t in past_trades if t['result'] == 'pending')
        
        # Remove all pending trades
        past_trades[:] = [t for t in past_trades if t['result'] != 'pending']
        
        pending_after = sum(1 for t in past_trades if t['result'] == 'pending')
        
        return jsonify({
            'success': True,
            'message': f'Cleared {pending_before} pending trade(s)',
            'pending_before': pending_before,
            'pending_after': pending_after
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trading/status', methods=['GET'])
def get_trading_status():
    """Get current trading status - bot always runs"""
    try:
        # Check if Telegram session exists
        session_file_exists = os.path.exists('po_vip_testing.session')
        session_journal_exists = os.path.exists('po_vip_testing.session-journal')
        
        # Check environment variables
        telegram_configured = bool(
            os.getenv('TELEGRAM_API_ID') and 
            os.getenv('TELEGRAM_API_HASH') and 
            os.getenv('TELEGRAM_PHONE')
        )
        
        return jsonify({
            'active': True,  # Bot always runs
            'config': {
                'trade_amount': get_trade_amount(),
                'is_demo': get_is_demo(),
                'multiplier': get_multiplier(),
                'global_step': global_martingale_step
            },
            'upcoming_trades': 0,  # Simplified version doesn't schedule trades
            'past_trades': len(past_trades),
            'diagnostics': {
                'session_file_exists': session_file_exists,
                'session_journal_exists': session_journal_exists,
                'telegram_configured': telegram_configured,
                'trading_thread_alive': trading_thread.is_alive() if trading_thread else False
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/trades/results', methods=['GET'])
def get_trade_results():
    """Get trade results with pagination (real or dummy data)"""
    try:
        global past_trades, data_mode, dummy_data_cache
        
        # Get pagination parameters
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Check if we're in dummy mode
        if data_mode == 'dummy':
            # Generate or return cached dummy trades
            if 'trades' not in dummy_data_cache:
                dummy_data_cache['trades'] = generate_dummy_trade_results()
            
            dummy_trades = dummy_data_cache['trades']
            total = len(dummy_trades)
            
            # Get paginated trades
            trades_slice = dummy_trades[offset:offset + limit]
            
            return jsonify({
                'total': total,
                'limit': limit,
                'offset': offset,
                'trades': trades_slice,
                'mode': 'dummy'
            })
        
        # Real mode - use existing logic
        total = len(past_trades)
        
        # Get paginated trades
        trades_slice = past_trades[offset:offset + limit]
        
        # Format trades for API response
        formatted_trades = []
        for trade in trades_slice:
            formatted_trade = {
                'time': trade.get('time', ''),
                'asset': trade.get('asset', ''),
                'direction': trade.get('direction', ''),
                'amount': trade.get('amount', 0),
                'step': trade.get('step', 0),
                'duration': trade.get('duration', 1),
                'result': trade.get('result', 'pending'),
                'order_id': trade.get('order_id', ''),
                'profit': 0  # Will be calculated from result
            }
            
            # Calculate profit based on result
            result = trade.get('result')
            amount = trade.get('amount', 0)
            
            if result == 'win':
                # Assuming 80% payout (adjust based on actual payout)
                formatted_trade['profit'] = round(amount * 0.8, 2)
            elif result == 'loss':
                formatted_trade['profit'] = round(-amount, 2)
            elif result == 'draw':
                # Draw returns the stake (no profit/loss)
                formatted_trade['profit'] = 0
            else:  # pending or failed
                formatted_trade['profit'] = 0
            
            formatted_trades.append(formatted_trade)
        
        return jsonify({
            'total': total,
            'limit': limit,
            'offset': offset,
            'trades': formatted_trades,
            'mode': 'real'
        })
    
    except Exception as e:
        print(f"ERROR: Error getting trade results: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades/upcoming', methods=['GET'])
def get_upcoming_trades():
    """Get upcoming scheduled trades (empty in simplified version)"""
    try:
        # Simplified main.py doesn't have upcoming_trades scheduling
        # Return empty list for API compatibility
        return jsonify({
            'total': 0,
            'trades': []
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades/analysis', methods=['GET'])
def get_trade_analysis():
    """Get trade analysis and statistics (real or dummy data)"""
    try:
        global past_trades, data_mode, dummy_data_cache, global_martingale_step
        
        # Check if we're in dummy mode
        if data_mode == 'dummy':
            # Generate or return cached dummy analysis
            if 'analysis' not in dummy_data_cache:
                dummy_data_cache['analysis'] = generate_dummy_analysis()
            else:
                # Slightly modify cached data to simulate changes
                import random
                cached = dummy_data_cache['analysis'].copy()
                cached['total_profit'] = round(cached['total_profit'] + random.uniform(-5, 5), 2)
                cached['current_trade_amount'] = round(random.uniform(1, 50) * (2.5 ** cached['current_step']), 2)
                dummy_data_cache['analysis'] = cached
            
            return dummy_data_cache['analysis']
        
        # Real mode - use existing logic
        if not past_trades:
            return jsonify({
                'total_trades': 0,
                'completed_trades': 0,
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'pending': 0,
                'failed': 0,
                'win_rate': 0,
                'total_profit': 0,
                'current_step': global_martingale_step,
                'current_trade_amount': get_trade_amount() * (get_multiplier() ** global_martingale_step),
                'mode': 'real'
            })
        
        # Count all result types
        wins = sum(1 for t in past_trades if t.get('result') == 'win')
        losses = sum(1 for t in past_trades if t.get('result') == 'loss')
        draws = sum(1 for t in past_trades if t.get('result') == 'draw')
        pending = sum(1 for t in past_trades if t.get('result') == 'pending')
        failed = sum(1 for t in past_trades if t.get('result') == 'failed')
        
        # Total completed trades (exclude pending and failed)
        completed = wins + losses + draws
        total = len(past_trades)
        
        # Win rate based on completed trades only (exclude draws)
        win_loss_total = wins + losses
        win_rate = (wins / win_loss_total * 100) if win_loss_total > 0 else 0
        
        # Calculate profit
        total_profit = 0
        for trade in past_trades:
            result = trade.get('result')
            amount = trade.get('amount', 0)
            
            if result == 'win':
                # Assuming 80% payout (adjust based on actual payout)
                total_profit += amount * 0.8
            elif result == 'loss':
                total_profit -= amount
            elif result == 'draw':
                # Draw returns the stake (no profit/loss)
                total_profit += 0
            # Pending and failed don't affect profit yet
        
        return jsonify({
            'total_trades': total,
            'completed_trades': completed,
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'pending': pending,
            'failed': failed,
            'win_rate': round(win_rate, 2),
            'total_profit': round(total_profit, 2),
            'current_step': global_martingale_step,
            'current_trade_amount': round(get_trade_amount() * (get_multiplier() ** global_martingale_step), 2),
            'mode': 'real'
        })
    
    except Exception as e:
        print(f"ERROR: Error in trade analysis: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/balance', methods=['GET'])
def get_balance():
    """Get current account balance from PocketOption or dummy data"""
    try:
        global client_balance, persistent_client_manager, data_mode, dummy_data_cache
        
        # Check if we're in dummy mode
        if data_mode == 'dummy':
            # Generate or return cached dummy data
            if 'balance' not in dummy_data_cache:
                dummy_data_cache['balance'] = generate_dummy_balance()
            else:
                # Slightly modify cached data to simulate changes
                import random
                cached = dummy_data_cache['balance'].copy()
                cached['demo_balance'] = round(cached['demo_balance'] + random.uniform(-10, 10), 2)
                cached['real_balance'] = round(cached['real_balance'] + random.uniform(-5, 5), 2)
                cached['timestamp'] = datetime.now().isoformat()
                dummy_data_cache['balance'] = cached
            
            return jsonify(dummy_data_cache['balance'])
        
        # Real mode - check cache age (cache for 5 seconds)
        if persistent_client_manager.last_balance_fetch:
            cache_age = (datetime.now() - persistent_client_manager.last_balance_fetch).total_seconds()
            if cache_age < 5:
                print(f"CACHE: Using cached balance (age: {cache_age:.1f}s)")
                return jsonify({
                    'demo_balance': persistent_client_manager.balance_cache['demo'],
                    'real_balance': persistent_client_manager.balance_cache['real'],
                    'currency': persistent_client_manager.balance_cache['currency'],
                    'timestamp': datetime.now().isoformat(),
                    'cached': True,
                    'mode': 'real'
                })
        
        print("SYNC: Fetching balance from PocketOption...")
        
        async def fetch_both_balances():
            results = {'demo': 0, 'real': 0, 'currency': 'USD', 'errors': []}
            
            # Fetch Demo Balance using persistent client
            try:
                print("DEMO: Getting demo balance...")
                demo_ssid = persistent_client_manager.get_ssid_for_mode(is_demo=True)
                demo_client = await persistent_client_manager.get_demo_client(demo_ssid)
                demo_balance = await asyncio.wait_for(demo_client.get_balance(), timeout=10.0)
                results['demo'] = demo_balance.balance
                results['currency'] = demo_balance.currency
                print(f"SUCCESS: Demo Balance: ${demo_balance.balance:.2f}")
            except asyncio.TimeoutError:
                error_msg = "Demo balance fetch timeout - SSID_DEMO may be expired"
                print(f"TIMEOUT: {error_msg}")
                results['errors'].append(error_msg)
                persistent_client_manager.demo_connected = False
            except Exception as e:
                error_msg = f"Error fetching demo balance: {str(e)}"
                print(f"ERROR: {error_msg}")
                results['errors'].append(error_msg)
                persistent_client_manager.demo_connected = False
            
            # Fetch Real Balance using persistent client
            try:
                print("REAL: Getting real balance...")
                real_ssid = persistent_client_manager.get_ssid_for_mode(is_demo=False)
                real_client = await persistent_client_manager.get_real_client(real_ssid)
                real_balance = await asyncio.wait_for(real_client.get_balance(), timeout=10.0)
                results['real'] = real_balance.balance
                print(f"SUCCESS: Real Balance: ${real_balance.balance:.2f}")
            except asyncio.TimeoutError:
                error_msg = "Real balance fetch timeout - SSID_REAL may be expired"
                print(f"TIMEOUT: {error_msg}")
                results['errors'].append(error_msg)
                persistent_client_manager.real_connected = False
            except Exception as e:
                error_msg = f"Error fetching real balance: {str(e)}"
                print(f"ERROR: {error_msg}")
                results['errors'].append(error_msg)
                persistent_client_manager.real_connected = False
            
            return results
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(fetch_both_balances())
        loop.close()
        
        # Check if both fetches failed
        if result['demo'] == 0 and result['real'] == 0 and result['errors']:
            error_message = '; '.join(result['errors'])
            print(f"⚠️ Balance fetch failed: {error_message}")
            return jsonify({
                'demo_balance': persistent_client_manager.balance_cache.get('demo', 0),
                'real_balance': persistent_client_manager.balance_cache.get('real', 0),
                'currency': 'USD',
                'error': f'Balance fetch timeout. {error_message}. Please update your SSID in Configuration.',
                'cached': True,
                'mode': 'real'
            }), 200  # Return 200 but with error message
        
        # Update cache
        if result['demo'] > 0 or result['real'] > 0:
            persistent_client_manager.balance_cache['demo'] = result['demo']
            persistent_client_manager.balance_cache['real'] = result['real']
            persistent_client_manager.balance_cache['currency'] = result['currency']
            persistent_client_manager.last_balance_fetch = datetime.now()
            
            # Also update global cache for backward compatibility
            client_balance['demo'] = result['demo']
            client_balance['real'] = result['real']
        
        print(f"CACHE: Balance cached - Demo: ${result['demo']:.2f}, Real: ${result['real']:.2f}")
        
        response_data = {
            'demo_balance': result['demo'],
            'real_balance': result['real'],
            'currency': result['currency'],
            'timestamp': datetime.now().isoformat(),
            'mode': 'real'
        }
        
        # Add warning if there were errors
        if result['errors']:
            response_data['warning'] = '; '.join(result['errors'])
        
        return jsonify(response_data)
    
    except Exception as e:
        print(f"ERROR: Balance fetch error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'demo_balance': client_balance.get('demo', 0),
            'real_balance': client_balance.get('real', 0),
            'currency': 'USD',
            'error': str(e),
            'cached': True,
            'mode': data_mode
        }), 500

def generate_dummy_balance():
    """Generate dummy balance data for testing"""
    import random
    return {
        'demo_balance': round(random.uniform(1000, 5000), 2),
        'real_balance': round(random.uniform(500, 2000), 2),
        'currency': 'USD',
        'timestamp': datetime.now().isoformat(),
        'dummy': True
    }

def generate_dummy_trade_results():
    """Generate dummy trade results for testing"""
    import random
    from datetime import datetime, timedelta
    
    results = []
    assets = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD']
    directions = ['call', 'put']
    outcomes = ['win', 'loss', 'draw']
    
    for i in range(10):  # Generate 10 dummy trades
        trade_time = datetime.now() - timedelta(minutes=random.randint(1, 120))
        result = random.choice(outcomes)
        amount = round(random.uniform(1, 50), 2)
        
        trade = {
            'time': trade_time.strftime('%H:%M:%S'),
            'asset': random.choice(assets),
            'direction': random.choice(directions),
            'amount': amount,
            'step': random.randint(0, 3),
            'duration': random.choice([1, 5, 15]),
            'result': result,
            'order_id': f"dummy_{random.randint(10000, 99999)}",
            'profit': round(amount * 0.8, 2) if result == 'win' else (-amount if result == 'loss' else 0),
            'dummy': True
        }
        results.append(trade)
    
    return results

def generate_dummy_analysis():
    """Generate dummy trade analysis data"""
    import random
    
    wins = random.randint(3, 8)
    losses = random.randint(2, 6)
    draws = random.randint(0, 2)
    total = wins + losses + draws
    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    
    return {
        'total_trades': total,
        'completed_trades': total,
        'wins': wins,
        'losses': losses,
        'draws': draws,
        'pending': 0,
        'failed': 0,
        'win_rate': round(win_rate, 2),
        'total_profit': round(random.uniform(-50, 100), 2),
        'current_step': random.randint(0, 3),
        'current_trade_amount': round(random.uniform(1, 50) * (2.5 ** random.randint(0, 3)), 2),
        'dummy': True
    }

def log_mode_change(mode, source='api'):
    """Log mode changes to Railway logs and storage"""
    try:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'mode': mode,
            'source': source,
            'hostname': os.getenv('RAILWAY_ENVIRONMENT', 'local'),
            'user_agent': request.headers.get('User-Agent', 'unknown') if 'request' in globals() else 'system'
        }
        
        # Log to console (Railway logs)
        print(f"MODE_CHANGE: {log_entry}")
        
        # Save to mode history file
        mode_history_file = 'mode_history.json'
        history = []
        
        if os.path.exists(mode_history_file):
            try:
                with open(mode_history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []
        
        history.append(log_entry)
        
        # Keep only last 50 entries
        if len(history) > 50:
            history = history[-50:]
        
        with open(mode_history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        logger.info(f"Data mode changed to: {mode} (source: {source})")
        
    except Exception as e:
        logger.error(f"Failed to log mode change: {e}")

@app.route('/api/mode', methods=['GET'])
def get_data_mode():
    """Get current data mode (real/dummy)"""
    global data_mode
    return jsonify({
        'current_mode': data_mode,
        'available_modes': ['real', 'dummy'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/mode', methods=['POST'])
def set_data_mode():
    """Set data mode (real/dummy)"""
    global data_mode, dummy_data_cache
    
    try:
        data = request.get_json()
        new_mode = data.get('mode')
        
        if new_mode not in ['real', 'dummy']:
            return jsonify({'error': 'Invalid mode. Use "real" or "dummy"'}), 400
        
        old_mode = data_mode
        data_mode = new_mode
        
        # Clear dummy cache when switching to real mode
        if new_mode == 'real':
            dummy_data_cache.clear()
        
        # Log the mode change
        log_mode_change(new_mode, 'api')
        
        # Pre-generate dummy data if switching to dummy mode
        if new_mode == 'dummy':
            dummy_data_cache['balance'] = generate_dummy_balance()
            dummy_data_cache['trades'] = generate_dummy_trade_results()
            dummy_data_cache['analysis'] = generate_dummy_analysis()
        
        return jsonify({
            'success': True,
            'message': f'Data mode changed from {old_mode} to {new_mode}',
            'current_mode': data_mode,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mode/history', methods=['GET'])
def get_mode_history():
    """Get mode change history"""
    try:
        mode_history_file = 'mode_history.json'
        
        if os.path.exists(mode_history_file):
            with open(mode_history_file, 'r') as f:
                history = json.load(f)
        else:
            history = []
        
        return jsonify({
            'history': history,
            'total': len(history)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/clear', methods=['POST'])
def clear_sessions():
    """Clear all sessions and create new session file"""
    try:
        from session_cleanup import save_sessions, get_session_stats
        import os
        
        session_file = 'sessions.json'
        
        # Delete existing session file if it exists
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
                print(f"Deleted existing session file: {session_file}")
            except Exception as e:
                print(f"Warning: Could not delete session file: {e}")
        
        # Create new empty session file
        empty_sessions = {}
        save_sessions(empty_sessions)
        
        # Get new session stats
        stats = get_session_stats()
        
        return jsonify({
            'success': True,
            'message': 'All sessions cleared successfully',
            'action': 'deleted_and_recreated',
            'session_file': session_file,
            'new_stats': stats,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to clear sessions'
        }), 500

@app.route('/api/config/trading', methods=['GET'])
def get_trading_config():
    """Get current trading configuration"""
    try:
        return jsonify({
            'success': True,
            'config': {
                'trade_amount': get_trade_amount(),
                'multiplier': get_multiplier(),
                'is_demo': get_is_demo(),
                'initial_balance': get_initial_balance(),
                'martingale_step': global_martingale_step
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config/trading', methods=['POST'])
def update_trading_config_endpoint():
    """Update trading configuration dynamically"""
    try:
        data = request.get_json()
        
        # Extract parameters
        trade_amount = data.get('trade_amount')
        multiplier = data.get('multiplier')
        is_demo = data.get('is_demo')
        initial_balance = data.get('initial_balance')
        
        # Validate inputs
        if trade_amount is not None:
            trade_amount = float(trade_amount)
            if trade_amount <= 0:
                return jsonify({'success': False, 'error': 'Trade amount must be positive'}), 400
        
        if multiplier is not None:
            multiplier = float(multiplier)
            if multiplier <= 0:
                return jsonify({'success': False, 'error': 'Multiplier must be positive'}), 400
        
        if initial_balance is not None:
            initial_balance = float(initial_balance)
            if initial_balance <= 0:
                return jsonify({'success': False, 'error': 'Initial balance must be positive'}), 400
        
        # Update configuration
        update_trading_config(
            trade_amount=trade_amount,
            multiplier=multiplier,
            is_demo=is_demo,
            initial_balance=initial_balance
        )
        
        return jsonify({
            'success': True,
            'message': 'Trading configuration updated successfully',
            'config': {
                'trade_amount': get_trade_amount(),
                'multiplier': get_multiplier(),
                'is_demo': get_is_demo(),
                'initial_balance': get_initial_balance(),
                'martingale_step': global_martingale_step
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config/trading/reset', methods=['POST'])
def reset_trading_config():
    """Reset trading configuration to defaults"""
    try:
        # Reset to defaults
        update_trading_config(
            trade_amount=5.0,
            multiplier=2.5,
            is_demo=True,
            initial_balance=10000.0
        )
        
        # Reset martingale step
        global global_martingale_step
        global_martingale_step = 0
        
        return jsonify({
            'success': True,
            'message': 'Trading configuration reset to defaults',
            'config': {
                'trade_amount': get_trade_amount(),
                'multiplier': get_multiplier(),
                'is_demo': get_is_demo(),
                'initial_balance': get_initial_balance(),
                'martingale_step': global_martingale_step
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def run_trading_bot():
    """Run trading bot continuously - uses dynamic configuration"""
    global trading_active
    
    loop = None
    try:
        # Get configuration from dynamic functions
        trade_amount = get_trade_amount()
        is_demo = get_is_demo()
        multiplier = get_multiplier()
        martingale_step = global_martingale_step
        
        print(f"START: Starting trading bot with config:")
        print(f"   Trade Amount: ${trade_amount} (dynamic)")
        print(f"   Account Type: {'DEMO' if is_demo else 'REAL'}")
        print(f"   Multiplier: {multiplier}x")
        print(f"   Starting Martingale Step: {martingale_step}")
        print(f"   Current Trade Amount: ${trade_amount * (multiplier ** martingale_step):.2f}")
        
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run trading bot main function
        loop.run_until_complete(telegram_main())
    
    except Exception as e:
        error_msg = str(e).lower()
        
        # Check for database lock error
        if 'database is locked' in error_msg or 'database' in error_msg:
            print(f"\nERROR: Database lock error detected: {e}")
            print("CLEANUP: Automatically cleaning up session files...")
            
            # Delete session files
            session_files = [
                'po_vip_testing.session',
                'po_vip_testing.session-journal'
            ]
            
            deleted_count = 0
            for session_file in session_files:
                if os.path.exists(session_file):
                    try:
                        os.remove(session_file)
                        deleted_count += 1
                        print(f"✓ Deleted {session_file}")
                    except Exception as del_error:
                        print(f"WARNING: Could not delete {session_file}: {del_error}")
            
            if deleted_count > 0:
                print(f"\nSUCCESS: Cleaned up {deleted_count} session file(s)")
                print("INFO: Session files deleted. Please restart server and verify OTP again.")
            else:
                print("\nWARNING: No session files found to delete")
        else:
            print(f"Trading bot error: {e}")
            import traceback
            traceback.print_exc()
        
        trading_active = False
    
    finally:
        # Properly cleanup event loop
        if loop:
            try:
                # Cancel all pending tasks
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                
                # Give tasks a chance to cleanup
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                
                # Close the loop
                loop.close()
            except Exception as cleanup_error:
                # Silently ignore cleanup errors
                pass

if __name__ == '__main__':
    # Get port from environment variable (Railway) or default to 5000
    port = int(os.getenv('PORT', 5000))
    
    print("=" * 60)
    print("START: Pocket Option Trading API Server")
    print("=" * 60)
    print(f"SERVER: Server starting on port {port}")
    print(f"FRONTEND: Frontend available at http://localhost:{port}")
    print("=" * 60)
    print("API: API Endpoints:")
    print("   POST /api/ssid - Set SSID")
    print("   POST /api/telegram/otp - Configure Telegram")
    print("   POST /api/trading/start - Start trading")
    print("   POST /api/trading/stop - Stop trading")
    print("   GET  /api/trading/status - Get status")
    print("   GET  /api/trades/results - Get trade results")
    print("   GET  /api/trades/upcoming - Get upcoming trades")
    print("   GET  /api/trades/analysis - Get trade analysis")
    print("   POST /api/sessions/clear - Clear all sessions")
    print("   GET  /api/sessions/status - Get session status")
    print("=" * 60)
    print("INFO: Quick Start:")
    print(f"   1. Open http://localhost:{port} in your browser")
    print("   2. Configure SSID and Telegram credentials")
    print("   3. Set trading parameters and click Start Trading")
    print("=" * 60)
    
    # AUTO-START TRADING BOT ON SERVER STARTUP
    # Bot starts automatically and runs continuously
    def auto_start_bot():
        """Auto-start trading bot in background"""
        import time
        time.sleep(5)  # Wait 5 seconds for server to be ready
        
        global trading_active, trading_thread
        
        # Always start bot
        try:
            print("\n" + "=" * 60)
            print("BOT: AUTO-STARTING TRADING BOT")
            print("=" * 60)
            
            # Get config from environment
            trade_amount = get_trade_amount()
            is_demo = get_is_demo()
            multiplier = get_multiplier()
            martingale_step = int(os.getenv('MARTINGALE_STEP', '0'))
            
            print(f"CONFIG: Configuration:")
            print(f"   Amount: ${trade_amount} (from .env)")
            print(f"   Mode: {'DEMO' if is_demo else 'REAL'}")
            print(f"   Multiplier: {multiplier}x")
            print(f"   Starting Step: {martingale_step}")
            print("=" * 60)
            
            trading_active = True
            trading_thread = threading.Thread(
                target=run_trading_bot,
                daemon=True
            )
            trading_thread.start()
            print("SUCCESS: Trading bot started automatically!")
            print("MONITOR: Bot is now monitoring Telegram signals")
            print("=" * 60 + "\n")
                
        except Exception as e:
            print(f"ERROR: Auto-start failed: {e}")
            print("INFO: Check your configuration in .env file")
            print("=" * 60 + "\n")
    
    # Start auto-start in background thread
    auto_start_thread = threading.Thread(target=auto_start_bot, daemon=True)
    auto_start_thread.start()
    
    # Disable debug mode in production
    is_production = os.getenv('RAILWAY_ENVIRONMENT') is not None
    app.run(host='0.0.0.0', port=port, debug=not is_production)
