import asyncio
import os
import re
import sys
import time
import csv
from pathlib import Path
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetHistoryRequest
from telethon import events
from datetime import datetime, timedelta
from typing import Dict

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import PocketOption API
from pocketoptionapi_async import AsyncPocketOptionClient
from pocketoptionapi_async.models import OrderDirection, OrderStatus

# Hardcoded credentials (directly in Python file)
API_ID = '34506083'
API_HASH = '5676893fa1c0fe15eca5dbbceb3ab6a2'
PHONE_NUMBER = '+12428018500'
STRING_SESSION = ''  # Will be set after session creation

# Hardcoded SSIDs
SSID_DEMO = '42["auth",{"session":"8kmju1f41cibg1vg5pihe37d7u","isDemo":1,"uid":116040367,"platform":2,"isFastHistory":true,"isOptimized":true}]'
SSID_REAL = '42["auth",{"session":"a:4:{s:10:\\"session_id\\";s:32:\\"2a8f01f1efeca20cc174c1b75eb6156a\\";s:10:\\"ip_address\\";s:14:\\"172.86.107.247\\";s:10:\\"user_agent\\";s:111:\\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36\\";s:13:\\"last_activity\\";i:1772807404;}3fed45de8f1ed072a8cabf7a07571f05","isDemo":0,"uid":116040367,"platform":2,"isFastHistory":true,"isOptimized":true}]'

# Channel usernames and IDs - Monitor Pocket Option VIP Signals channel
CHANNELS = [
    {'username': 'Pocket_Option_Signals_Vip', 'id': None, 'name': 'Pocket Option Signals VIP'}
]

# Dynamic trading configuration (can be updated via API)
dynamic_trade_amount = 5.0
dynamic_multiplier = 2.5
dynamic_is_demo = True
dynamic_initial_balance = 10000.0

def get_trade_amount():
    """Get current trade amount - dynamic"""
    return dynamic_trade_amount

def get_multiplier():
    """Get multiplier - dynamic"""
    return dynamic_multiplier

def get_is_demo():
    """Get account type - dynamic"""
    return dynamic_is_demo

def get_initial_balance():
    """Get initial balance - dynamic"""
    return dynamic_initial_balance

def update_trading_config(trade_amount=None, multiplier=None, is_demo=None, initial_balance=None):
    """Update trading configuration dynamically"""
    global dynamic_trade_amount, dynamic_multiplier, dynamic_is_demo, dynamic_initial_balance
    
    if trade_amount is not None:
        dynamic_trade_amount = float(trade_amount)
    if multiplier is not None:
        dynamic_multiplier = float(multiplier)
    if is_demo is not None:
        dynamic_is_demo = bool(is_demo)
    if initial_balance is not None:
        dynamic_initial_balance = float(initial_balance)

# Global martingale step
global_martingale_step = 0

# Track trades
past_trades = []

# Persistent client
persistent_client = None

# CSV folder
CSV_FOLDER = 'trade_results'

def ensure_csv_folder():
    """Create CSV folder if it doesn't exist"""
    Path(CSV_FOLDER).mkdir(exist_ok=True)

def get_csv_filename():
    """Get CSV filename for current date"""
    today = datetime.now().strftime('%Y-%m-%d')
    return os.path.join(CSV_FOLDER, f'trades_{today}.csv')

def save_trade_to_csv(trade_data: Dict):
    """Save trade result to CSV file"""
    try:
        ensure_csv_folder()
        csv_file = get_csv_filename()
        
        file_exists = os.path.exists(csv_file)
        
        headers = [
            'timestamp', 'date', 'time', 'asset', 'direction', 
            'amount', 'step', 'duration', 'result', 'profit_loss',
            'balance_before', 'balance_after', 'multiplier'
        ]
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(trade_data)
        
        print(f"Trade saved to CSV: {csv_file}")
        
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def log_message(message: str):
    """Log message to console and file"""
    print(message)
    try:
        with open('telegram/trading_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"{message}\n")
    except:
        pass

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
        log_message(f"Base Amount (from .env): ${trade_amount:.2f}")
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
    
    # Check if bot is already running
    try:
        import psutil
        current_pid = os.getpid()
        python_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'main.py' in cmdline and proc.info['pid'] != current_pid:
                        python_processes.append(proc.info['pid'])
            except:
                pass
        
        if python_processes:
            log_message(f"Bot is already running (PIDs: {python_processes})")
            log_message("Please stop other instances first")
            return
    except ImportError:
        pass  # psutil not available, skip check
    
    # Pre-connect to PocketOption
    log_message("\n" + "="*60)
    log_message("POCKET OPTION TRADING BOT")
    log_message("="*60)
    log_message(f"Channels: {len(CHANNELS)} channels")
    for ch in CHANNELS:
        log_message(f"  - {ch['name']} (ID: {ch['id']})")
    log_message(f"Account: {'DEMO' if get_is_demo() else 'REAL'}")
    
    # Show hardcoded configuration
    trade_amount_parsed = get_trade_amount()
    log_message(f"Trade Amount: ${trade_amount_parsed} (hardcoded)")
    log_message(f"Initial Amount: ${trade_amount_parsed}")
    
    log_message(f"Multiplier: {get_multiplier()}x (hardcoded)")
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
        
    except Exception as e:
        log_message(f"Telegram connection error: {e}")
        log_message("Attempting to create new session...")
        await create_session_if_needed()
        return

async def create_session_if_needed():
    """Create Telegram session if credentials are available"""
    if not all([API_ID, API_HASH, PHONE_NUMBER]):
        log_message("❌ Missing Telegram credentials in .env:")
        log_message(f"   API_ID: {'SET' if API_ID else 'NOT SET'}")
        log_message(f"   API_HASH: {'SET' if API_HASH else 'NOT SET'}")
        log_message(f"   PHONE: {'SET' if PHONE_NUMBER else 'NOT SET'}")
        log_message("Please set these in your .env file or frontend")
        return
    
    try:
        log_message("📱 Creating new Telegram session...")
        log_message(f"   Phone: {PHONE_NUMBER}")
        log_message(f"   API ID: {API_ID}")
        
        # Create client for session creation
        client = TelegramClient('po_vip_testing', API_ID, API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            log_message("📲 Sending OTP code...")
            result = await client.send_code_request(PHONE_NUMBER)
            log_message(f"✅ OTP sent to {PHONE_NUMBER}")
            log_message("🔢 Please enter OTP code manually:")
            log_message("   Option 1: Use frontend to enter OTP")
            log_message("   Option 2: Enter OTP here directly")
            
            # Try to get OTP from console input
            try:
                otp_code = input("Enter OTP code (or press Enter to skip): ").strip()
                if otp_code:
                    log_message(f"🔓 Verifying OTP: {otp_code}")
                    await client.sign_in(PHONE_NUMBER, otp_code, result.phone_code_hash)
                    log_message("✅ OTP verified successfully!")
                else:
                    log_message("⏭️ Skipping manual OTP - use frontend")
                    log_message("🌐 Open http://localhost:5000 to complete setup")
                    await client.disconnect()
                    return
            except KeyboardInterrupt:
                log_message("⏭️ OTP input cancelled - use frontend")
                log_message("🌐 Open http://localhost:5000 to complete setup")
                await client.disconnect()
                return
            except Exception as e:
                log_message(f"❌ OTP verification failed: {e}")
                await client.disconnect()
                return
        else:
            log_message("✅ Already authorized - creating string session...")
            
        # Create string session
        string_session = StringSession.save(client.session)
        
        # Set global variable directly
        global STRING_SESSION
        STRING_SESSION = string_session
        
        log_message("✅ String session created and set in memory")
        await client.disconnect()
        
    except Exception as e:
        log_message(f"❌ Session creation failed: {e}")
        log_message("Please check your credentials and try again")
    
    # Connect to ALL channels
    channels = []
    for channel_info in CHANNELS:
        try:
            # Try to get channel by ID first
            if channel_info['id']:
                try:
                    channel = await client.get_entity(channel_info['id'])
                    channels.append(channel)
                    log_message(f"Connected to: {channel.title} (ID: {channel_info['id']})")
                except Exception as e:
                    # Try by username if ID fails
                    if channel_info['username']:
                        log_message(f"Failed by ID, trying username @{channel_info['username']}...")
                        channel = await client.get_entity(channel_info['username'])
                        channels.append(channel)
                        log_message(f"Connected to: {channel.title}")
                    else:
                        log_message(f"Failed to connect to {channel_info['name']}: {e}")
            elif channel_info['username']:
                channel = await client.get_entity(channel_info['username'])
                channels.append(channel)
                log_message(f"✅ Connected to: {channel.title}")
        except Exception as e:
            log_message(f"Error connecting to {channel_info['name']}: {e}")
    
    if not channels:
        log_message("Failed to connect to any channels")
        return
    
    log_message(f"Monitoring {len(channels)} channel(s)")
    
    # Get recent messages from all channels (don't execute, just for context)
    total_messages = 0
    for channel in channels:
        try:
            recent_time = datetime.now() - timedelta(minutes=30)
            messages = await client(GetHistoryRequest(
                peer=channel,
                limit=50,
                offset_date=recent_time,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0
            ))
            total_messages += len(messages.messages)
        except Exception as e:
            log_message(f"Could not get history from {channel.title}: {e}")
    
    log_message(f"Found {total_messages} recent messages across all channels")
    
    # Start cleanup task in background
    asyncio.create_task(cleanup_stale_trades())
    log_message("Started automatic stale trade cleanup (every 60s)")
    
    last_message_ids = {channel.id: 0 for channel in channels}
    
    # Listen for NEW messages from ALL channels
    @client.on(events.NewMessage(chats=channels))
    async def handle_new_message(event):
        channel_title = event.chat.title if hasattr(event.chat, 'title') else 'Unknown'
        
        if event.message.id > last_message_ids.get(event.chat_id, 0):
            last_message_ids[event.chat_id] = event.message.id
            
            log_message(f"\nNEW MESSAGE from [{channel_title}]: {event.message.message[:100]}")
            
            # Process message and place trade if signal is complete
            await process_message(event.message.message)
    
    log_message("\nWaiting for signals from ALL channels...\n")
    
    # Keep alive
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
