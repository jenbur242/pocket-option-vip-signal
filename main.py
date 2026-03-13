import asyncio
import os
import re
import sys
import time
import csv
from pathlib import Path
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetHistoryRequest
from telethon import events
from datetime import datetime, timedelta
from typing import Dict

# Load environment variables
load_dotenv()

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import PocketOption API
from pocketoptionapi_async import AsyncPocketOptionClient
from pocketoptionapi_async.models import OrderDirection, OrderStatus

# Hardcoded credentials (directly in Python file)
API_ID = '34506083'
API_HASH = '5676893fa1c0fe15eca5dbbceb3ab6a2'
PHONE_NUMBER = '+12428018500'
STRING_SESSION = '1AZWarzkBu3VuwqWk96RSig3o6wO73aGKaGF3TkEtOMMXwTQQWNjGX2tU5t3i6eIHbBesaMAQWpU3PfjnXNleOmBIv4QXVvn5LnMNq36dGkLw9dCk7zOvvbuETBtzS4sNdcAISyNQfjg21-p2m31f0C65oTxXlI8ndW6bHmbXaXBm18fIHNOp-6G8AKF7iklIrCWuG8EkMPs-BfSLMrmzuoGbuh8ymqecpuM1TW2nhz1BHQpswQDX3BwTA1f_IkbWoGn0ePSml8_Zz5xJmNiiShbaWRjuRnACiHt7u6zFIAjHRpS1ds3jRv7GgUjIJlUERRA2gWKrl9hxuATvY03ah0kmP8zcWLI='  # Working session from po_vip_testing_1773343014.session

# Hardcoded SSIDs
SSID_DEMO = '42["auth",{"session":"8kmju1f41cibg1vg5pihe37d7u","isDemo":1,"uid":116040367,"platform":2,"isFastHistory":true,"isOptimized":true}]'
SSID_REAL = '42["auth",{"session":"a:4:{s:10:\\"session_id\\";s:32:\\"2a8f01f1efeca20cc174c1b75eb6156a\\";s:10:\\"ip_address\\";s:14:\\"172.86.107.247\\";s:10:\\"user_agent\\";s:111:\\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36\\";s:13:\\"last_activity\\";i:1772807404;}3fed45de8f1ed072a8cabf7a07571f05","isDemo":0,"uid":116040367,"platform":2,"isFastHistory":true,"isOptimized":true}]'

# Channel usernames and IDs - Monitor Pocket Option VIP Signals channel
CHANNELS = [
    'Pocket_Option_Signals_Vip'  # Use username directly instead of dict
]

# Trading configuration from .env
TRADE_AMOUNT = float(os.getenv('TRADE_AMOUNT', '5.0'))
MULTIPLIER = float(os.getenv('MULTIPLIER', '2.5'))
IS_DEMO = os.getenv('IS_DEMO', 'true').lower() == 'true'
INITIAL_BALANCE = float(os.getenv('INITIAL_BALANCE', '10000.0'))

def get_trade_amount():
    """Get current trade amount - from .env"""
    return TRADE_AMOUNT

def get_multiplier():
    """Get multiplier - from .env"""
    return MULTIPLIER

def get_is_demo():
    """Get account type - from .env"""
    return IS_DEMO

def get_initial_balance():
    """Get initial balance - from .env"""
    return INITIAL_BALANCE

# Global martingale step
global_martingale_step = 0

# Track trades
past_trades = []

# Persistent client
persistent_client = None

def save_trade_to_csv(trade_data):
    """Save trade to CSV file in both local and Railway storage"""
    try:
        from datetime import datetime
        from pathlib import Path
        
        # Create directories in both local and Railway storage
        csv_dirs = ['telegram/trades', '/tmp/csv']
        
        for csv_dir in csv_dirs:
            Path(csv_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate filename with current date
        date_str = datetime.now().strftime('%Y-%m-%d')
        csv_file = f'telegram/trades/trades_{date_str}.csv'
        railway_csv_file = f'/tmp/csv/trades_{date_str}.csv'
        
        # Save to both locations
        for file_path in [csv_file, railway_csv_file]:
            try:
                file_exists = os.path.exists(file_path)
                
                with open(file_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    if not file_exists:
                        writer.writerow([
                            'timestamp', 'asset', 'direction', 'amount', 
                            'duration', 'result', 'profit', 'balance'
                        ])
                    
                    writer.writerow([
                        trade_data.get('timestamp', ''),
                        trade_data.get('asset', ''),
                        trade_data.get('direction', ''),
                        trade_data.get('amount', ''),
                        trade_data.get('duration', ''),
                        trade_data.get('result', ''),
                        trade_data.get('profit', ''),
                        trade_data.get('balance', '')
                    ])
                
                print(f"Trade saved to CSV: {file_path}")
                
            except Exception as e:
                print(f"Error saving to {file_path}: {e}")
        
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def log_message(message: str):
    """Log message to console and Railway storage"""
    try:
        # Remove problematic Unicode characters for Windows console
        import re
        # Replace common problematic Unicode characters with ASCII equivalents
        message = message.replace('📱', '[PHONE]').replace('📲', '[SMS]').replace('✅', '[OK]').replace('❌', '[ERROR]').replace('🔢', '[INPUT]').replace('🔓', '[VERIFY]').replace('📋', '[INFO]').replace('🧹', '[CLEAN]').replace('⚠️', '[WARNING]')
        print(message)
    except:
        # Fallback to plain print if encoding fails
        try:
            print(str(message).encode('ascii', 'ignore').decode('ascii'))
        except:
            print("LOG MESSAGE ENCODING ERROR")
    
    # Log to Railway storage
    try:
        # Ensure Railway storage directories exist
        import os
        from pathlib import Path
        
        # Create directories in Railway storage
        log_dirs = ['/tmp/logs/telegram', 'telegram/logs']
        for log_dir in log_dirs:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # Log to both local and Railway storage
        log_files = ['telegram/trading_log.txt', '/tmp/logs/telegram/trading_log.txt']
        
        for log_file in log_files:
            try:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {message}\n")
            except:
                pass
                
    except Exception as e:
        print(f"Storage logging error: {e}")

def map_asset_name(pair: str) -> str:
    """Map asset pair to Pocket Option format"""
    clean_pair = pair.replace(' ', '').replace('/', '').upper()
    
    if 'OTC' in pair.upper():
        if clean_pair.endswith('OTC'):
            base_name = clean_pair[:-3]
            return f"{base_name}_otc"
        else:
            return f"{clean_pair}_otc"
    else:
        return clean_pair

async def get_persistent_client():
    """Get or create persistent client"""
    global persistent_client
    
    if persistent_client and persistent_client.is_connected:
        return persistent_client
    
    # Get SSID based on current demo mode
    is_demo = get_is_demo()
    
    if is_demo:
        ssid = SSID_DEMO  # Use hardcoded SSID_DEMO
    else:
        ssid = SSID_REAL  # Use hardcoded SSID_REAL
        if not ssid:
            raise Exception("SSID_REAL not configured")
    log_message("Connecting to PocketOption...")
    
    client = AsyncPocketOptionClient(
        ssid=ssid,
        is_demo=is_demo,
        persistent_connection=False,
        auto_reconnect=True,
        enable_logging=True
    )
    
    connected = await asyncio.wait_for(client.connect(), timeout=30.0)
    
    if not connected:
        raise Exception("Connection failed")
    
    await asyncio.sleep(1)
    
    try:
        balance = await asyncio.wait_for(client.get_balance(), timeout=10.0)
        log_message(f"Balance: ${balance.balance:.2f} {balance.currency}")
    except Exception as e:
        log_message(f"Balance fetch failed: {e}")
    
    log_message("Connected to PocketOption!")
    
    persistent_client = client
    return client

async def check_trade_result(order_id: str, duration_minutes: int):
    """Check trade result after completion"""
    global past_trades, global_martingale_step
    
    try:
        client = await get_persistent_client()
        
        wait_time = duration_minutes * 60 + 30
        
        log_message(f"Waiting for trade {order_id} result (max {wait_time}s)...")
        
        win_result = await client.check_win(
            order_id=order_id,
            max_wait_time=wait_time
        )
        
        if win_result and win_result.get("completed"):
            result_type = win_result.get("result", "unknown")
            profit = win_result.get("profit", 0)
            
            log_message(f"Result: {result_type.upper()} | Profit: ${profit:.2f}")
            
            # Update past_trades
            for trade in reversed(past_trades):
                if trade.get('order_id') == order_id:
                    trade['result'] = result_type
                    
                    # Save to CSV
                    csv_data = {
                        'timestamp': datetime.now().isoformat(),
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'asset': trade['asset'],
                        'direction': trade['direction'],
                        'amount': trade['amount'],
                        'step': trade['step'],
                        'duration': trade.get('duration', 1),
                        'result': result_type,
                        'profit_loss': profit,
                        'balance_before': '',
                        'balance_after': '',
                        'multiplier': get_multiplier()  # Use dynamic function
                    }
                    save_trade_to_csv(csv_data)
                    break
            
            # Update martingale step
            if result_type == 'win':
                global_martingale_step = 0
                past_trades[:] = [t for t in past_trades if t['result'] == 'pending']
                log_message(f"\n{'='*60}")
                log_message(f"WIN! Reset martingale step to 0")
                log_message(f"Next trade amount: ${get_trade_amount():.2f}")
                log_message(f"Ready for new asset signal")
                log_message(f"{'='*60}\n")
            elif result_type == 'draw':
                past_trades[:] = [t for t in past_trades if t.get('order_id') != order_id]
                log_message(f"\n{'='*60}")
                log_message(f"DRAW! No change to step {global_martingale_step}")
                next_amount = get_trade_amount() * (get_multiplier() ** global_martingale_step)
                log_message(f"Next trade amount: ${next_amount:.2f}")
                log_message(f"Same asset kept: {last_signal['asset']}")
                log_message(f"{'='*60}\n")
            elif result_type == 'loss':
                if global_martingale_step < 7:
                    global_martingale_step += 1
                    next_amount = get_trade_amount() * (get_multiplier() ** global_martingale_step)
                    log_message(f"\n{'='*60}")
                    log_message(f"LOSS! Martingale step increased to {global_martingale_step}")
                    log_message(f"Next trade amount: ${next_amount:.2f}")
                    log_message(f"Same asset kept: {last_signal['asset']} - waiting for next direction")
                    log_message(f"{'='*60}\n")
                else:
                    global_martingale_step = 0
                    log_message(f"\n{'='*60}")
                    log_message(f"Max steps reached (7), reset to 0")
                    log_message(f"Next trade amount: ${get_trade_amount():.2f}")
                    log_message(f"Same asset kept: {last_signal['asset']}")
                    log_message(f"{'='*60}\n")
        else:
            log_message(f"Result timeout for order {order_id}")
            
    except Exception as e:
        log_message(f"Error checking result: {e}")

async def place_trade(asset: str, direction: str, duration: int):
    """Place trade immediately - SIMPLE AND DIRECT"""
    global past_trades, global_martingale_step
    
    duration_minutes = duration  # Rename for clarity
    
    try:
        # Check if there are pending trades - PREVENT DUPLICATE TRADES
        pending_trades = [t for t in past_trades if t['result'] == 'pending']
        pending_count = len(pending_trades)
        
        if pending_count > 0:
            # Check if pending trades are stale (older than 5 minutes - reduced from 10)
            import time
            current_time = time.time()
            stale_trades = []
            
            for trade in pending_trades:
                # Check if trade has a timestamp
                if 'placed_timestamp' in trade:
                    age_seconds = current_time - trade['placed_timestamp']
                    # If trade is older than 5 minutes, consider it stale
                    if age_seconds > 300:
                        stale_trades.append(trade)
                        log_message(f"Found stale pending trade (age: {age_seconds:.0f}s), removing...")
                else:
                    # If no timestamp, consider it stale (old format)
                    stale_trades.append(trade)
                    log_message(f"Found pending trade without timestamp, removing...")
            
            # Remove stale trades
            if stale_trades:
                past_trades[:] = [t for t in past_trades if t not in stale_trades]
                pending_count = sum(1 for t in past_trades if t['result'] == 'pending')
                log_message(f"Cleaned {len(stale_trades)} stale trade(s)")
            
            # Recheck pending count after cleanup
            if pending_count > 0:
                log_message(f"Skipping trade - {pending_count} pending trade(s) already active")
                log_message(f"Waiting for current trade to complete before placing new one")
                return
        
        # Get client
        client = await get_persistent_client()
        
        # Map asset name
        asset_name = map_asset_name(asset)
        
        # Get current trading configuration (dynamic from environment)
        trade_amount = get_trade_amount()
        multiplier = get_multiplier()
        
        # Calculate amount with martingale
        current_step = global_martingale_step
        current_amount = trade_amount * (multiplier ** current_step)
        
        log_message(f"\n{'='*60}")
        log_message(f"TRADE AMOUNT CALCULATION - STEP {current_step}")
        log_message(f"{'='*60}")
        log_message(f"Base Amount: ${trade_amount:.2f}")
        log_message(f"Multiplier: {multiplier}x")
        log_message(f"Current Martingale Step: {current_step}")
        log_message(f"Formula: ${trade_amount:.2f} × ({multiplier}^{current_step})")
        log_message(f"FINAL TRADE AMOUNT: ${current_amount:.2f}")
        log_message(f"{'='*60}\n")
        
        # Determine direction
        order_direction = OrderDirection.CALL if direction.upper() == 'BUY' else OrderDirection.PUT
        
        log_message(f"\n{'='*60}")
        log_message(f"PLACING TRADE")
        log_message(f"{'='*60}")
        log_message(f"Asset: {asset_name}")
        log_message(f"Direction: {direction.upper()}")
        log_message(f"Amount: ${current_amount:.2f}")
        log_message(f"Duration: {duration_minutes} min")
        log_message(f"Martingale Step: {current_step}")
        log_message(f"{'='*60}")
        
        # Place order - EXACT SAME AS test_trade.py
        order_result = await client.place_order(
            asset=asset_name,
            amount=current_amount,
            direction=order_direction,
            duration=duration_minutes * 60
        )
        
        if order_result and order_result.status in [OrderStatus.ACTIVE, OrderStatus.PENDING]:
            log_message(f"Order placed successfully!")
            log_message(f"   Order ID: {order_result.order_id}")
            log_message(f"   Status: {order_result.status.value}")
            log_message(f"   Placed at: {order_result.placed_at.strftime('%H:%M:%S')}")
            log_message(f"   Expires at: {order_result.expires_at.strftime('%H:%M:%S')}")
            
            # Add to past trades with timestamp
            import time
            past_trades.append({
                'time': datetime.now().strftime('%H:%M:%S'),
                'asset': asset_name,
                'direction': direction.upper(),
                'amount': current_amount,
                'step': current_step,
                'duration': duration_minutes,
                'result': 'pending',
                'order_id': order_result.order_id,
                'placed_timestamp': time.time()  # Add timestamp for stale detection
            })
            
            # Check result in background
            asyncio.create_task(check_trade_result(order_result.order_id, duration_minutes))
            
        else:
            error_msg = order_result.error_message if order_result and order_result.error_message else 'Unknown error'
            log_message(f"Trade failed: {error_msg}")
            
    except Exception as e:
        log_message(f"Error placing trade: {e}")
        import traceback
        traceback.print_exc()

def parse_signal(message_text: str) -> Dict:
    """Parse signal from Telegram message - IMPROVED REGEX PATTERNS"""
    signal = {'asset': None, 'direction': None, 'duration': None}
    
    # Strip whitespace from message
    message_text = message_text.strip()
    
    # Multiple asset patterns (try in order of specificity)
    asset_patterns = [
        r'Pair:\s*([A-Z]+/[A-Z]+(?:\s+OTC)?)',
        r'([A-Z]+/[A-Z]+(?:\s+OTC)?)',            # Without "Pair:" prefix
        r'([A-Z]{6,}(?:\s+OTC)?)',               # 6+ letters with OTC (EURUSD OTC)
        r'([A-Z]{6,}(?:[A-Z/]+)?)',               # 6+ letters (EURGBP, EURUSD) or with slash
    ]
    
    for pattern in asset_patterns:
        asset_match = re.search(pattern, message_text, re.IGNORECASE)
        if asset_match:
            signal['asset'] = asset_match.group(1).strip()
            break
    
    # Multiple time patterns (try in order of specificity)
    time_patterns = [
        r'⌛[️]?\s*time:\s*(\d+)\s*min',      # Original format with emoji
        r'time:\s*(\d+)\s*min',             # Without emoji
        r'(\d+)\s*min',                     # Just "X min"
        r'duration:\s*(\d+)\s*min',         # Duration format
    ]
    
    for pattern in time_patterns:
        time_match = re.search(pattern, message_text, re.IGNORECASE)
        if time_match:
            signal['duration'] = int(time_match.group(1))
            break
    
    # Default to 2 minutes if no time found
    if signal['duration'] is None:
        signal['duration'] = 2
    
    # Multiple direction patterns (try in order of specificity)
    direction_patterns = [
        r'^(Buy|Sell)\s*$',                 # Original format
        r'\b(Buy|Sell|CALL|PUT)\b',         # Any trading direction
        r'(Buy|CALL)',
        r'(Sell|PUT)',
        r'^([Bb])\s*$',                     # Single letter B for Buy
        r'^([Ss])\s*$',                     # Single letter S for Sell
    ]
    
    for pattern in direction_patterns:
        direction_match = re.search(pattern, message_text, re.IGNORECASE | re.MULTILINE)
        if direction_match:
            direction = direction_match.group(1).upper()
            # Normalize single letters and CALL/PUT to BUY/SELL
            if direction == 'B':
                direction = 'BUY'
            elif direction == 'S':
                direction = 'SELL'
            elif direction == 'CALL':
                direction = 'BUY'
            elif direction == 'PUT':
                direction = 'SELL'
            signal['direction'] = direction
            break
    
    return signal

# Store last signal for direction matching - KEEP ASSET UNTIL WIN
last_signal = {'asset': None, 'duration': None}

# Track last processed direction signal to prevent duplicates
last_direction_signal = {'asset': None, 'direction': None, 'timestamp': None}

# Lock to prevent concurrent trade placement
trade_placement_lock = asyncio.Lock()

# Flag to track if a trade is currently being placed
trade_in_progress = False

async def process_message(message_text: str):
    """Process Telegram message and place trade if complete signal"""
    global last_signal, last_direction_signal, trade_in_progress
    
    signal = parse_signal(message_text)
    
    # If we got asset and duration, store it (update the asset)
    if signal['asset'] and signal['duration']:
        last_signal['asset'] = signal['asset']
        last_signal['duration'] = signal['duration']
        log_message(f"Signal received: {signal['asset']} - {signal['duration']} min")
    
    # If we got direction and have stored asset/duration, place trade
    if signal['direction'] and last_signal['asset'] and last_signal['duration']:
        log_message(f"Direction received: {signal['direction']}")
        
        # Check if trade is already in progress (before acquiring lock)
        if trade_in_progress:
            log_message(f"Skipping - trade already in progress")
            return
        
        # Use lock to prevent concurrent trade placement
        async with trade_placement_lock:
            import time
            current_time = time.time()
            
            # Double-check inside lock
            if trade_in_progress:
                log_message(f"Skipping - trade already in progress (double-check)")
                return
            
            # Check if this exact signal was just processed (within 3 seconds)
            if (last_direction_signal['asset'] == last_signal['asset'] and
                last_direction_signal['direction'] == signal['direction'] and
                last_direction_signal['timestamp'] and
                current_time - last_direction_signal['timestamp'] < 3):
                log_message(f"Skipping duplicate direction signal (already processed {current_time - last_direction_signal['timestamp']:.1f}s ago)")
                return
            
            # Set flag to prevent other trades
            trade_in_progress = True
            
            try:
                # Update last direction signal
                last_direction_signal['asset'] = last_signal['asset']
                last_direction_signal['direction'] = signal['direction']
                last_direction_signal['timestamp'] = current_time
                
                # Place trade immediately
                await place_trade(
                    asset=last_signal['asset'],
                    direction=signal['direction'],
                    duration=last_signal['duration']
                )
            finally:
                # Always clear the flag when done
                trade_in_progress = False
        
        # DON'T clear last signal - keep it for martingale on same asset
        # It will only be replaced when a new asset signal comes

async def cleanup_stale_trades():
    """Periodic task to clean up stale pending trades"""
    global past_trades
    
    while True:
        try:
            await asyncio.sleep(60)  # Check every 60 seconds
            
            import time
            current_time = time.time()
            
            pending_trades = [t for t in past_trades if t['result'] == 'pending']
            if not pending_trades:
                continue
            
            stale_trades = []
            for trade in pending_trades:
                if 'placed_timestamp' in trade:
                    age_seconds = current_time - trade['placed_timestamp']
                    # Remove trades older than 5 minutes
                    if age_seconds > 300:
                        stale_trades.append(trade)
                else:
                    # Remove trades without timestamp (old format)
                    stale_trades.append(trade)
            
            if stale_trades:
                past_trades[:] = [t for t in past_trades if t not in stale_trades]
                log_message(f"Auto-cleanup: Removed {len(stale_trades)} stale pending trade(s)")
                
        except Exception as e:
            log_message(f"Cleanup task error: {e}")

async def main():
    """Main function - Listen to Telegram and place trades"""
    global STRING_SESSION
    
    # Pre-connect to PocketOption
    log_message("\n" + "="*60)
    log_message("POCKET OPTION TRADING BOT")
    log_message("="*60)
    log_message(f"Channels: {len(CHANNELS)} channels")
    for ch in CHANNELS:
        log_message(f"  - {ch} (monitoring)")
    log_message(f"Account: {'DEMO' if get_is_demo() else 'REAL'}")
    
    # Show configuration from .env
    trade_amount_parsed = get_trade_amount()
    log_message(f"Trade Amount: ${trade_amount_parsed} (from .env)")
    log_message(f"Initial Amount: ${trade_amount_parsed}")
    
    log_message(f"Multiplier: {get_multiplier()}x (from .env)")
    log_message("="*60)
    
    # Show martingale calculation table
    log_message("\n" + "="*60)
    log_message("MARTINGALE AMOUNT TABLE (8 Steps)")
    log_message("="*60)
    multiplier = get_multiplier()
    for step in range(8):
        amount = trade_amount_parsed * (multiplier ** step)
        log_message(f"Step {step}: ${amount:>10.2f}")
    log_message("="*60 + "\n")
    
    try:
        await get_persistent_client()
    except Exception as e:
        log_message(f"Failed to connect to PocketOption: {e}")
        return
    
    # Check if session exists, if not create one
    if not STRING_SESSION:
        log_message("No string session found - creating new session...")
        await create_session_if_needed()
        # Session will be set by create_session_if_needed function
        
        if not STRING_SESSION:
            log_message("Failed to create session - please check your credentials")
            return
    
    # Connect to Telegram using string session
    log_message("Using hardcoded string session")
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    
    try:
        # Connect first, then check if authorized
        await client.connect()
        
        # Check if already authorized
        if not await client.is_user_authorized():
            log_message("String session invalid - recreating session...")
            await create_session_if_needed()
            # Session will be set by create_session_if_needed function
            if STRING_SESSION:
                client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
                await client.connect()
                if not await client.is_user_authorized():
                    log_message("Session creation failed - please check credentials")
                    return
            else:
                log_message("Failed to recreate session")
                return
        
        log_message("Telegram session authorized successfully")
        log_message("Ready to monitor trading signals")
        
        # Set up message handlers
        from telethon import events
        
        @client.on(events.NewMessage(chats=CHANNELS))
        async def handle_new_message(event):
            """Handle new messages from channels"""
            try:
                message_text = event.message.message
                if message_text:
                    log_message(f"Received message: {message_text[:100]}...")
                    await process_message(message_text)
            except Exception as e:
                log_message(f"Message handling error: {e}")
        
        # Start the client
        await client.start()
        log_message("Telegram client started - monitoring for signals...")
        
        # Keep the client running
        await client.run_until_disconnected()
        
    except Exception as e:
        log_message(f"Telegram connection error: {e}")
        log_message("Attempting to create new session...")
        await create_session_if_needed()
        return

async def create_session_if_needed():
    """Create Telegram session if credentials are available"""
    global STRING_SESSION
    
    if not all([API_ID, API_HASH, PHONE_NUMBER]):
        log_message("❌ Missing Telegram credentials")
        log_message(f"   API_ID: {'SET' if API_ID else 'NOT SET'}")
        log_message(f"   API_HASH: {'SET' if API_HASH else 'NOT SET'}")
        log_message(f"   PHONE: {'SET' if PHONE_NUMBER else 'NOT SET'}")
        log_message("Please check credentials in main.py")
        return
    
    try:
        log_message("[PHONE] Creating new Telegram session...")
        log_message(f"   Phone: {PHONE_NUMBER}")
        
        # Create client for session creation (use unique session name)
        import time
        session_name = f'po_vip_testing_{int(time.time())}'
        client = TelegramClient(session_name, API_ID, API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            log_message("[SMS] Sending OTP code...")
            result = await client.send_code_request(PHONE_NUMBER)
            log_message(f"[OK] OTP sent to {PHONE_NUMBER}")
            
            # Check if we got phone_code_hash
            if hasattr(result, 'phone_code_hash') and result.phone_code_hash:
                log_message(f"[INFO] Phone code hash received: {result.phone_code_hash}")
                log_message("[INPUT] Please enter OTP code manually:")
            else:
                log_message("[ERROR] Failed to get phone code hash from Telegram")
                await client.disconnect()
                return
            
            # Get OTP from console input
            try:
                import sys
                print("Enter OTP code: ", end='', flush=True)
                otp_code = sys.stdin.readline().strip()
                if otp_code:
                    log_message(f"[VERIFY] Verifying OTP: {otp_code}")
                    log_message(f"[INFO] Using phone_code_hash: {result.phone_code_hash}")
                    
                    try:
                        await client.sign_in(PHONE_NUMBER, otp_code, phone_code_hash=result.phone_code_hash)
                        log_message("[OK] OTP verified successfully!")
                    except Exception as sign_error:
                        log_message(f"[ERROR] Sign in error: {sign_error}")
                        log_message("[ERROR] OTP verification failed - please check the code")
                        await client.disconnect()
                        return
                else:
                    log_message("[ERROR] No OTP code entered")
                    await client.disconnect()
                    return
            except KeyboardInterrupt:
                log_message("[ERROR] OTP input cancelled")
                await client.disconnect()
                return
            except Exception as e:
                log_message(f"[ERROR] OTP verification failed: {e}")
                await client.disconnect()
                return
        else:
            log_message("✅ Already authorized - creating string session...")
            
        # Create string session
        string_session = StringSession.save(client.session)
        
        # Set global variable directly
        STRING_SESSION = string_session
        
        log_message("[OK] String session created and saved to memory")
        
        # Clean up the temporary session file
        try:
            import os
            if os.path.exists(session_name + '.session'):
                os.remove(session_name + '.session')
                log_message(f"[CLEAN] Cleaned up temporary session file: {session_name}.session")
        except Exception as cleanup_error:
            log_message(f"[WARNING] Could not clean up session file: {cleanup_error}")
        
        await client.disconnect()
        
    except Exception as e:
        log_message(f"[ERROR] Session creation failed: {e}")
        log_message("Please check your credentials and try again")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
