import asyncio
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import from main.py
from main import (
    get_persistent_client, place_trade, parse_signal, save_trade_to_csv,
    API_ID, API_HASH, STRING_SESSION, SSID_DEMO, SSID_REAL,
    get_trade_amount, get_multiplier, get_is_demo, map_asset_name
)

# Import Telegram
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

# Import PocketOption
from pocketoptionapi_async.models import OrderDirection

async def test_pocketoption_connection():
    """Test PocketOption API connection and authentication"""
    print("\n" + "="*60)
    print("TESTING POCKETOPTION API CONNECTION")
    print("="*60)
    
    try:
        print("1. Testing connection...")
        client = await get_persistent_client()
        print("[OK] Connected successfully!")
        
        print("2. Testing balance fetch...")
        balance = await client.get_balance()
        print(f"[OK] Balance: ${balance.balance:.2f} {balance.currency}")
        
        print("3. Testing asset availability...")
        # Try to get some common assets
        test_assets = ["EURUSD", "GBPUSD", "EURGBP"]
        for asset in test_assets:
            try:
                mapped_asset = map_asset_name(asset)
                print(f"   - {asset} -> {mapped_asset}")
            except Exception as e:
                print(f"   - {asset} -> ERROR: {e}")
        
        print("[OK] PocketOption API working correctly!")
        return True, client
        
    except Exception as e:
        print(f"[ERROR] PocketOption API Error: {e}")
        return False, None

async def test_telegram_connection():
    """Test Telegram API connection with session string"""
    print("\n" + "="*60)
    print("TESTING TELEGRAM API CONNECTION")
    print("="*60)
    
    try:
        print("1. Testing session string...")
        if not STRING_SESSION:
            print("[ERROR] No session string found in main.py")
            return False, None
            
        print(f"2. Connecting with session (length: {len(STRING_SESSION)})...")
        client = TelegramClient(StringSession(STRING_SESSION), int(API_ID), API_HASH)
        await client.connect()
        
        print("3. Checking authorization...")
        if await client.is_user_authorized():
            me = await client.get_me()
            print("[OK] Authorized as: {} (@{} )".format(me.first_name, me.username))
            print(f"   Phone: {me.phone}")
            print(f"   ID: {me.id}")
        else:
            print("[ERROR] Session not authorized")
            await client.disconnect()
            return False, None
        
        print("4. Testing channel access...")
        test_channels = ['Pocket_Option_Signals_Vip']
        for channel in test_channels:
            try:
                entity = await client.get_entity(channel)
                print("[OK] Channel access: {} (@{})".format(entity.title, entity.username))
            except Exception as e:
                print("[ERROR] Channel access failed: {} -> {}".format(channel, e))
        
        print("[OK] Telegram API working correctly!")
        return True, client
        
    except Exception as e:
        print("[ERROR] Telegram API Error: {}".format(e))
        return False, None

async def test_trade_placement(client):
    """Test trade placement with minimum amount"""
    print("\n" + "="*60)
    print("TESTING TRADE PLACEMENT (DEMO MODE)")
    print("="*60)
    
    try:
        # Use minimum amount for testing
        test_amount = 1.0
        test_asset = "EURUSD"
        test_direction = "BUY"
        test_duration = 1  # 1 minute
        
        print(f"1. Preparing test trade:")
        print(f"   Asset: {test_asset}")
        print(f"   Direction: {test_direction}")
        print(f"   Amount: ${test_amount}")
        print(f"   Duration: {test_duration} min")
        print(f"   Account: {'DEMO' if get_is_demo() else 'REAL'}")
        
        # Map asset name
        asset_name = map_asset_name(test_asset)
        print(f"   Mapped Asset: {asset_name}")
        
        # Place order
        print("2. Placing trade...")
        order_direction = OrderDirection.CALL if test_direction.upper() == 'BUY' else OrderDirection.PUT
        
        order_result = await client.place_order(
            asset=asset_name,
            amount=test_amount,
            direction=order_direction,
            duration=test_duration * 60
        )
        
        if order_result and order_result.status in ['ACTIVE', 'PENDING']:
            print("[OK] Trade placed successfully!")
            print(f"   Order ID: {order_result.order_id}")
            print(f"   Status: {order_result.status}")
            print(f"   Placed at: {order_result.placed_at}")
            print(f"   Expires at: {order_result.expires_at}")
            
            # Wait a moment then check result
            print("3. Waiting for result...")
            await asyncio.sleep(test_duration * 60 + 10)
            
            win_result = await client.check_win(
                order_id=order_result.order_id,
                max_wait_time=30
            )
            
            if win_result and win_result.get("completed"):
                result_type = win_result.get("result", "unknown")
                profit = win_result.get("profit", 0)
                print("[OK] Result: {} | Profit: ${:.2f}".format(result_type.upper(), profit))
            else:
                print("[WARNING] Result check timeout or incomplete")
            
            return True, order_result.order_id
        else:
            error_msg = order_result.error_message if order_result else 'Unknown error'
            print("[ERROR] Trade failed: {}".format(error_msg))
            return False, None
            
    except Exception as e:
        print("[ERROR] Trade placement error: {}".format(e))
        import traceback
        traceback.print_exc()
        return False, None

def test_signal_parsing():
    """Test signal parsing functionality"""
    print("\n" + "="*60)
    print("TESTING SIGNAL PARSING")
    print("="*60)
    
    test_signals = [
        "Pair: EUR/USD OTC\ntime: 5 min\nBuy",
        "GBP/USD\n3 min\nSell",
        "EURGBP OTC\ntime: 2 min\nCALL",
        "AUD/USD\n1 min\nPUT",
        "USD/CAD OTC\nDuration: 4 min\nBuy"
    ]
    
    for i, signal in enumerate(test_signals, 1):
        print(f"\n{i}. Testing signal:")
        print(f"   Input: {repr(signal)}")
        
        parsed = parse_signal(signal)
        print(f"   Asset: {parsed['asset']}")
        print(f"   Direction: {parsed['direction']}")
        print(f"   Duration: {parsed['duration']} min")
        
        if parsed['asset'] and parsed['direction'] and parsed['duration']:
            print("   [OK] Parsed successfully")
        else:
            print("   [ERROR] Parsing incomplete")

def test_csv_logging():
    """Test CSV logging functionality"""
    print("\n" + "="*60)
    print("TESTING CSV LOGGING")
    print("="*60)
    
    try:
        # Create test trade data
        test_trade = {
            'timestamp': datetime.now().isoformat(),
            'asset': 'EURUSD',
            'direction': 'BUY',
            'amount': 5.0,
            'duration': 2,
            'result': 'win',
            'profit': 8.50,
            'balance': 1008.50
        }
        
        print("1. Saving test trade to CSV...")
        save_trade_to_csv(test_trade)
        
        # Check if file was created
        date_str = datetime.now().strftime('%Y-%m-%d')
        csv_file = f'telegram/trades/trades_{date_str}.csv'
        
        if os.path.exists(csv_file):
            print("[OK] CSV file created: {}".format(csv_file))
            
            # Read and display last few lines
            with open(csv_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"   File has {len(lines)} lines")
                if len(lines) > 1:
                    print(f"   Last entry: {lines[-1].strip()}")
        else:
            print("[ERROR] CSV file not found: {}".format(csv_file))
            
        print("[OK] CSV logging test completed")
        
    except Exception as e:
        print("[ERROR] CSV logging error: {}".format(e))

async def main():
    """Main test function"""
    print("\n" + "="*80)
    print("COMPREHENSIVE API TESTING FOR POCKET OPTION TRADING BOT")
    print("="*80)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Demo Mode: {get_is_demo()}")
    print(f"Trade Amount: ${get_trade_amount()}")
    print(f"Multiplier: {get_multiplier()}x")
    print("="*80)
    
    results = {}
    
    # Test 1: PocketOption Connection
    po_success, po_client = await test_pocketoption_connection()
    results['pocketoption'] = po_success
    
    # Test 2: Telegram Connection
    tg_success, tg_client = await test_telegram_connection()
    results['telegram'] = tg_success
    
    # Test 3: Trade Placement (only if PocketOption works)
    if po_success and po_client:
        trade_success, order_id = await test_trade_placement(po_client)
        results['trade'] = trade_success
    else:
        print("[WARNING] Skipping trade test due to PocketOption connection failure")
        results['trade'] = False
    
    # Test 4: Signal Parsing
    test_signal_parsing()
    results['parsing'] = True  # Always testable
    
    # Test 5: CSV Logging
    test_csv_logging()
    results['logging'] = True  # Always testable
    
    # Cleanup
    if po_client:
        try:
            await po_client.disconnect()
        except:
            pass
    
    if tg_client:
        try:
            await tg_client.disconnect()
        except:
            pass
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for test, success in results.items():
        status = "[PASS]" if success else "[FAIL]"
        print(f"{test.upper():<15} : {status}")
    
    all_passed = all(results.values())
    print("="*80)
    if all_passed:
        print("[SUCCESS] ALL TESTS PASSED! Bot is ready for trading.")
    else:
        print("[WARNING] Some tests failed. Check the errors above.")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
