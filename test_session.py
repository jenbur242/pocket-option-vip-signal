#!/usr/bin/env python3
"""
Test PocketOption Session String Connection
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from pocketoptionapi_async import AsyncPocketOptionClient
    from pocketoptionapi_async.models import OrderDirection, OrderStatus
    print("[OK] PocketOption API imported successfully")
except ImportError as e:
    print(f"[ERROR] PocketOption API import error: {e}")
    sys.exit(1)

# Hardcoded credentials from main.py
PHONE_NUMBER = '+12428018500'
STRING_SESSION = '1AZWarzkBuyPe9BnmmNJBJyG0R4fb9EItkxpNvjV6sNBiMjN-gK1hkjz9XpBkxFV92uT_Yxj2I_ZKFzJ0d8GWj9DkicZXiFSSqips6XmXzzVscklLd2pZb4k6ctz6LTE6z8b_uUgRpEZzectHQpSEq5BreaiSin9OYbpBAiHm1CGlf8KUWZVVz7nzlnlzPq54u7pQY44Q8I6DGiFJN9_ay3K883tv1xB9SZ1jJsB_BYeovtN2tqchrWTfyc4pX5rT7nlK3js3ZhQRNhuNXQXBHWFubLIKYaelQq7pONm4ZUyMCnxYNP6a_CaEG1ByCf36OunherYkP5KNoydmTNds3lD6-1h1hGQ='

# Hardcoded SSIDs
SSID_DEMO = '42["auth",{"session":"8kmju1f41cibg1vg5pihe37d7u","isDemo":1,"uid":116040367,"platform":2,"isFastHistory":true,"isOptimized":true}]'
SSID_REAL = '42["auth",{"session":"a:4:{s:10:\\"session_id\\";s:32:\\"2a8f01f1efeca20cc174c1b75eb6156a\\";s:10:\\"ip_address\\";s:14:\\"172.86.107.247\\";s:10:\\"user_agent\\";s:111:\\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36\\";s:13:\\"last_activity\\";i:1772807404;}3fed45de8f1ed072a8cabf7a07571f05","isDemo":0,"uid":116040367,"platform":2,"isFastHistory":true,"isOptimized":true}]'

def log_message(message: str):
    """Log message with timestamp"""
    import datetime
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}")

async def test_demo_connection():
    """Test demo account connection"""
    print("\n" + "="*60)
    print("TESTING DEMO ACCOUNT CONNECTION")
    print("="*60)
    
    try:
        log_message("Creating demo client...")
        client = AsyncPocketOptionClient(
            ssid=SSID_DEMO,
            is_demo=True,
            persistent_connection=False,
            auto_reconnect=True,
            enable_logging=True
        )
        
        log_message("Connecting to demo account...")
        connected = await asyncio.wait_for(client.connect(), timeout=30.0)
        
        if connected:
            log_message("[OK] Demo connection successful!")
            
            # Test balance
            try:
                balance = await asyncio.wait_for(client.get_balance(), timeout=10.0)
                log_message(f"[OK] Demo Balance: ${balance.balance:.2f} {balance.currency}")
            except Exception as e:
                log_message(f"[ERROR] Demo balance fetch failed: {e}")
            
            # Test asset availability
            try:
                assets = await asyncio.wait_for(client.get_assets(), timeout=10.0)
                log_message(f"[OK] Available assets: {len(assets)}")
                
                # Check for AUDUSD
                audusd_available = any('AUDUSD' in str(asset) for asset in assets)
                log_message(f"[OK] AUDUSD available: {audusd_available}")
                
                if audusd_available:
                    log_message("[OK] Asset mapping should work for AUDUSD")
                else:
                    log_message("[ERROR] AUDUSD not available - this might be the issue!")
                    
            except Exception as e:
                log_message(f"[ERROR] Asset fetch failed: {e}")
            
            # Test small trade (demo)
            try:
                log_message("Testing demo trade placement...")
                order_result = await asyncio.wait_for(
                    client.place_order(
                        asset="AUDUSD",
                        amount=1.0,
                        direction=OrderDirection.CALL,
                        duration=120  # 2 minutes
                    ),
                    timeout=10.0
                )
                
                if order_result and order_result.status in [OrderStatus.ACTIVE, OrderStatus.PENDING]:
                    log_message(f"[OK] Demo trade successful! Order ID: {order_result.order_id}")
                else:
                    error_msg = order_result.error_message if order_result and order_result.error_message else 'Unknown error'
                    log_message(f"[ERROR] Demo trade failed: {error_msg}")
                    
            except Exception as e:
                log_message(f"[ERROR] Demo trade exception: {e}")
            
        else:
            log_message("[ERROR] Demo connection failed!")
            
    except Exception as e:
        log_message(f"[ERROR] Demo connection error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            await client.disconnect()
            log_message("Demo client disconnected")
        except:
            pass

async def test_real_connection():
    """Test real account connection"""
    print("\n" + "="*60)
    print("TESTING REAL ACCOUNT CONNECTION")
    print("="*60)
    
    try:
        log_message("Creating real client...")
        client = AsyncPocketOptionClient(
            ssid=SSID_REAL,
            is_demo=False,
            persistent_connection=False,
            auto_reconnect=True,
            enable_logging=True
        )
        
        log_message("Connecting to real account...")
        connected = await asyncio.wait_for(client.connect(), timeout=30.0)
        
        if connected:
            log_message("✅ Real connection successful!")
            
            # Test balance
            try:
                balance = await asyncio.wait_for(client.get_balance(), timeout=10.0)
                log_message(f"✅ Real Balance: ${balance.balance:.2f} {balance.currency}")
            except Exception as e:
                log_message(f"❌ Real balance fetch failed: {e}")
            
            # Test asset availability
            try:
                assets = await asyncio.wait_for(client.get_assets(), timeout=10.0)
                log_message(f"✅ Available assets: {len(assets)}")
                
                # Check for AUDUSD
                audusd_available = any('AUDUSD' in str(asset) for asset in assets)
                log_message(f"✅ AUDUSD available: {audusd_available}")
                    
            except Exception as e:
                log_message(f"❌ Asset fetch failed: {e}")
            
        else:
            log_message("❌ Real connection failed!")
            
    except Exception as e:
        log_message(f"❌ Real connection error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            await client.disconnect()
            log_message("Real client disconnected")
        except:
            pass

async def main():
    """Main test function"""
    print("[TEST] PocketOption Session Test")
    print("Testing both demo and real account connections...")
    
    # Test demo first (safer)
    await test_demo_connection()
    
    # Wait a bit
    await asyncio.sleep(2)
    
    # Test real (if needed)
    # await test_real_connection()
    
    print("\n" + "="*60)
    print("[TEST COMPLETE]")
    print("="*60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
