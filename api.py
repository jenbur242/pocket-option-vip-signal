#!/usr/bin/env python3
"""
API Server for Pocket Option Trading Bot
- Runs main.py continuously
- Detects trading signals
- Places trades automatically
- Shows results via API
- Stores logs and sessions in Railway bucket
"""

import os
import json
import asyncio
import threading
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import sys

# Initialize Flask app
app = Flask(__name__)

# Configure logging properly for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)

# Get Railway logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CORS(app)

# Global variables for bot status
bot_status = {
    'running': False,
    'started_at': None,
    'last_signal': None,
    'total_trades': 0,
    'winning_trades': 0,
    'losing_trades': 0,
    'current_balance': 0.0,
    'last_trade': None,
    'telegram_connected': False,
    'pocketoption_connected': False,
    'error': None
}

# Bot thread
bot_thread = None
bot_loop = None

def ensure_railway_storage():
    """Ensure Railway bucket storage directories exist"""
    try:
        # Railway storage directories
        storage_dirs = [
            '/tmp/logs',
            '/tmp/sessions', 
            '/tmp/trades',
            '/tmp/csv'
        ]
        
        for dir_path in storage_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"Storage directory ready: {dir_path}")
            
        # Create symlinks from local to Railway storage
        if not os.path.exists('/tmp/logs/telegram'):
            os.makedirs('/tmp/logs/telegram', exist_ok=True)
            if os.path.exists('telegram'):
                os.symlink('/tmp/logs/telegram', 'telegram/logs', target_is_directory=True)
                
    except Exception as e:
        logger.error(f"Storage setup error: {e}")

def backup_to_railway():
    """Backup important files to Railway storage"""
    try:
        import shutil
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Backup session files
        if os.path.exists('po_vip_testing.session'):
            shutil.copy2('po_vip_testing.session', f'/tmp/sessions/session_{timestamp}.session')
            
        # Backup trading log
        if os.path.exists('telegram/trading_log.txt'):
            shutil.copy2('telegram/trading_log.txt', f'/tmp/logs/trading_log_{timestamp}.txt')
            
        # Backup CSV files
        if os.path.exists('telegram/trades'):
            for csv_file in os.listdir('telegram/trades'):
                if csv_file.endswith('.csv'):
                    shutil.copy2(f'telegram/trades/{csv_file}', f'/tmp/csv/{csv_file}')
                    
        logger.info(f"Backup completed: {timestamp}")
        
    except Exception as e:
        logger.error(f"Backup error: {e}")

async def run_bot_continuously():
    """Run the trading bot continuously"""
    global bot_status
    
    try:
        logger.info("Starting continuous trading bot...")
        
        # Update status immediately
        bot_status['running'] = True
        bot_status['started_at'] = datetime.now().isoformat()
        bot_status['error'] = None
        
        # Import and run main bot
        from main import main as main_bot
        
        # Update status for connections
        try:
            # Run the bot
            await main_bot()
            
            # If we get here, the bot finished successfully
            bot_status['running'] = False
            
        except Exception as e:
            logger.error(f"Bot error: {e}")
            bot_status['error'] = str(e)
            bot_status['running'] = False
    except Exception as e:
        logger.error(f"Bot startup error: {e}")
        bot_status['error'] = str(e)
        bot_status['running'] = False
    finally:
        bot_status['running'] = False

def start_bot_thread():
    """Start bot in background thread"""
    global bot_thread, bot_loop
    
    if bot_thread and bot_thread.is_alive():
        return False, "Bot is already running"
    
    def run_in_thread():
        global bot_loop
        bot_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(bot_loop)
        bot_loop.run_until_complete(run_bot_continuously())
    
    bot_thread = threading.Thread(target=run_in_thread, daemon=True)
    bot_thread.start()
    
    return True, "Bot started successfully"

def stop_bot():
    """Stop the running bot"""
    global bot_thread, bot_loop
    
    if bot_loop:
        bot_loop.call_soon_threadsafe(bot_loop.stop)
    
    if bot_thread and bot_thread.is_alive():
        bot_thread.join(timeout=5)
    
    bot_status['running'] = False
    return True, "Bot stopped"

def update_bot_status_from_logs():
    """Update bot status by reading recent logs"""
    try:
        # Read recent logs to determine actual status
        log_files = ['/tmp/logs/telegram/trading_log.txt', 'telegram/trading_log.txt']
        
        for log_file in log_files:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-50:]  # Last 50 lines for better balance tracking
                    
                    # Check for connection status
                    telegram_connected = any('Telegram session authorized successfully' in line for line in recent_lines)
                    pocketoption_connected = any('Connected to PocketOption!' in line for line in recent_lines)
                    bot_ready = any('Ready to monitor trading signals' in line for line in recent_lines)
                    
                    # Update status if bot is actually running
                    if telegram_connected and pocketoption_connected and bot_ready:
                        bot_status['telegram_connected'] = True
                        bot_status['pocketoption_connected'] = True
                        bot_status['running'] = True
                        
                        # Enhanced balance extraction with multiple patterns
                        balance_patterns = [
                            'Balance: $',
                            'Balance updated: $',
                            'balance: $',
                            'Balance: $49101.57 USD',
                            'Balance: $49096.57 USD'
                        ]
                        
                        for line in recent_lines:
                            for pattern in balance_patterns:
                                if pattern in line:
                                    try:
                                        # Extract balance with better parsing
                                        if 'USD' in line:
                                            # Pattern: "Balance: $49101.57 USD"
                                            balance_part = line.split('$')[1].split(' ')[0]
                                            if balance_part.replace('.', '').isdigit():
                                                bot_status['current_balance'] = float(balance_part)
                                                logger.info(f"Updated balance from logs: ${bot_status['current_balance']}")
                                                return
                                        elif 'updated:' in line.lower():
                                            # Pattern: "Balance updated: $49096.57"
                                            balance_part = line.split('$')[1].split(' ')[0]
                                            if balance_part.replace('.', '').isdigit():
                                                bot_status['current_balance'] = float(balance_part)
                                                logger.info(f"Updated balance from logs: ${bot_status['current_balance']}")
                                                return
                                    except Exception as e:
                                        logger.debug(f"Balance parsing error: {e}")
                                        continue
                                
        # If no balance found in logs, try to get from PocketOption directly
        if bot_status.get('pocketoption_connected') and bot_status.get('current_balance', 0) == 0:
            try:
                # Import main to get persistent client
                import sys
                sys.path.append('.')
                from main import get_persistent_client
                
                # Try to get fresh balance
                import asyncio
                async def get_fresh_balance():
                    try:
                        client = await get_persistent_client()
                        if client and hasattr(client, 'get_balance'):
                            balance_result = await client.get_balance()
                            if balance_result and hasattr(balance_result, 'balance'):
                                fresh_balance = float(balance_result.balance)
                                bot_status['current_balance'] = fresh_balance
                                logger.info(f"Updated balance from API: ${fresh_balance}")
                                return fresh_balance
                    except Exception as e:
                        logger.error(f"Fresh balance error: {e}")
                        return None
                
                # Run the async function
                loop = asyncio.new_event_loop()
                fresh_balance = loop.run_until_complete(get_fresh_balance())
                
                if fresh_balance:
                    bot_status['current_balance'] = fresh_balance
                    
            except Exception as e:
                logger.error(f"Balance update error: {e}")
                                
    except Exception as e:
        logger.error(f"Status update error: {e}")

# API Routes
@app.route('/')
def index():
    """Serve frontend dashboard"""
    try:
        # Get current directory and construct full path
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        frontend_path = os.path.join(current_dir, 'frontend.html')
        
        with open(frontend_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({
            'status': 'Pocket Option Trading Bot API',
            'version': '1.0.0',
            'message': 'Frontend not found',
            'endpoints': [
                '/status',
                '/start', 
                '/stop',
                '/trades',
                '/balance',
                '/logs',
                '/signals'
            ]
        })

@app.route('/api')
def api_info():
    """API Status"""
    return jsonify({
        'status': 'Pocket Option Trading Bot API',
        'version': '1.0.0',
        'endpoints': [
            '/status',
            '/start', 
            '/stop',
            '/trades',
            '/balance',
            '/logs',
            '/signals'
        ]
    })

@app.route('/status')
def get_status():
    """Get bot status"""
    # Update status from logs first
    update_bot_status_from_logs()
    return jsonify(bot_status)

@app.route('/start', methods=['POST'])
def start_bot():
    """Start the trading bot"""
    success, message = start_bot_thread()
    return jsonify({
        'success': success,
        'message': message,
        'status': bot_status
    })

@app.route('/stop', methods=['POST'])
def stop_bot_api():
    """Stop the trading bot"""
    success, message = stop_bot()
    return jsonify({
        'success': success,
        'message': message,
        'status': bot_status
    })

@app.route('/trades')
def get_trades():
    """Get recent trades"""
    try:
        trades = []
        
        # Read from CSV files
        if os.path.exists('telegram/trades'):
            for csv_file in os.listdir('telegram/trades'):
                if csv_file.endswith('.csv'):
                    try:
                        import csv
                        with open(f'telegram/trades/{csv_file}', 'r') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                trades.append({
                                    'timestamp': row.get('timestamp', ''),
                                    'asset': row.get('asset', ''),
                                    'direction': row.get('direction', ''),
                                    'amount': row.get('amount', ''),
                                    'duration': row.get('duration', ''),
                                    'result': row.get('result', ''),
                                    'profit': row.get('profit', '0')
                                })
                    except Exception as e:
                        logger.error(f"Error reading {csv_file}: {e}")
        
        # Sort by timestamp (most recent first)
        trades.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({
            'trades': trades[:50],  # Return last 50 trades
            'total_trades': len(trades)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/balance')
def get_balance():
    """Get current balance"""
    try:
        # Force balance update first
        update_bot_status_from_logs()
        
        # Try to get fresh balance from PocketOption
        if bot_status.get('pocketoption_connected'):
            try:
                import sys
                sys.path.append('.')
                from main import get_persistent_client
                import asyncio
                
                async def get_fresh_balance():
                    try:
                        client = await get_persistent_client()
                        if client and hasattr(client, 'get_balance'):
                            balance_result = await client.get_balance()
                            if balance_result and hasattr(balance_result, 'balance'):
                                fresh_balance = float(balance_result.balance)
                                bot_status['current_balance'] = fresh_balance
                                logger.info(f"Fresh balance from API: ${fresh_balance}")
                                return {
                                    'balance': fresh_balance,
                                    'currency': 'USD',
                                    'timestamp': datetime.now().isoformat(),
                                    'source': 'live_api'
                                }
                    except Exception as e:
                        logger.error(f"Fresh balance error: {e}")
                        return None
                
                # Run the async function
                loop = asyncio.new_event_loop()
                fresh_balance_data = loop.run_until_complete(get_fresh_balance())
                
                if fresh_balance_data:
                    return jsonify(fresh_balance_data)
                else:
                    # Fallback to cached balance
                    return jsonify({
                        'balance': bot_status.get('current_balance', 0.0),
                        'currency': 'USD',
                        'timestamp': datetime.now().isoformat(),
                        'source': 'cached'
                    })
            except Exception as e:
                logger.error(f"Balance endpoint error: {e}")
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify({
                'error': 'PocketOption not connected'
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logs')
def get_logs():
    """Get recent logs"""
    try:
        logs = []
        
        if os.path.exists('telegram/trading_log.txt'):
            with open('telegram/trading_log.txt', 'r') as f:
                lines = f.readlines()
                logs = [line.strip() for line in lines[-100:]]  # Last 100 lines
        
        return jsonify({
            'logs': logs,
            'total_logs': len(logs),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/signals')
def get_signals():
    """Get recent trading signals"""
    try:
        # This would parse recent messages from Telegram
        # For now, return placeholder
        return jsonify({
            'signals': [],
            'last_signal': bot_status.get('last_signal'),
            'message': 'Signal detection is active in the running bot'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/backup', methods=['POST'])
def create_backup():
    """Create backup to Railway storage"""
    try:
        backup_to_railway()
        return jsonify({
            'success': True,
            'message': 'Backup created successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check for Railway"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'bot_running': bot_status['running'],
        'storage_ready': os.path.exists('/tmp/logs')
    })

# Update bot status from main.py
def update_bot_status(signal=None, trade=None, balance=None):
    """Update bot status from main.py"""
    if signal:
        bot_status['last_signal'] = signal
    if trade:
        bot_status['last_trade'] = trade
        bot_status['total_trades'] += 1
        if trade.get('result') == 'WIN':
            bot_status['winning_trades'] += 1
        elif trade.get('result') == 'LOSS':
            bot_status['losing_trades'] += 1
    if balance:
        bot_status['current_balance'] = balance

if __name__ == '__main__':
    # Setup Railway storage
    ensure_railway_storage()
    
    # Start bot automatically
    logger.info("Starting API server with auto-bot...")
    start_bot_thread()
    
    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
