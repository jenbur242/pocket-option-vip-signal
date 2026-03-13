#!/usr/bin/env python3
"""
Test trading signal placement
"""

import asyncio
import time
from main import process_message, place_trade, log_message

async def test_trading_signal():
    """Test if bot can place trades with asset and direction"""
    
    print("=== TESTING TRADE SIGNAL PLACEMENT ===")
    print()
    
    # Test 1: Asset signal only (should store but not trade)
    print("1. Testing ASSET signal only...")
    asset_signal = "EUR/USD OTC 5 min"
    result = await process_message(asset_signal)
    print(f"   Result: {result}")
    print()
    
    # Test 2: Direction signal with stored asset (should place trade)
    print("2. Testing DIRECTION signal with stored asset...")
    direction_signal = "CALL"
    result = await process_message(direction_signal)
    print(f"   Result: {result}")
    print()
    
    # Test 3: Complete signal in one message (should place trade immediately)
    print("3. Testing COMPLETE signal in one message...")
    complete_signal = "EUR/USD OTC 5 min CALL"
    result = await process_message(complete_signal)
    print(f"   Result: {result}")
    print()
    
    # Wait a bit to see if trade is processed
    print("4. Waiting 3 seconds for trade processing...")
    await asyncio.sleep(3)
    
    print("=== TEST COMPLETED ===")
    print("Check logs and trading results in the dashboard")

if __name__ == "__main__":
    asyncio.run(test_trading_signal())
