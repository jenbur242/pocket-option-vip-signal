# How main.py Reads Messages and Filters Assets & Directions

## 📨 Message Processing Flow

### 1. **Telegram Message Reception**
```python
@client.on(events.NewMessage(chats=CHANNELS))
async def handle_new_message(event):
    """Handle new messages from channels"""
    message_text = event.message.message
    if message_text:
        log_message(f"Received message: {message_text[:100]}...")
        await process_message(message_text)
```

### 2. **Signal Parsing Function**
```python
def parse_signal(message_text: str) -> Dict:
    signal = {'asset': None, 'direction': None, 'duration': None}
    message_text = message_text.strip()
```

## 🔍 Asset Filtering Patterns

### **Asset Detection (in order of specificity):**
```python
asset_patterns = [
    r'Pair:\s*([A-Z]+/[A-Z]+(?:\s+OTC)?)',    # "Pair: EUR/USD OTC"
    r'([A-Z]+/[A-Z]+(?:\s+OTC)?)',            # "EUR/USD OTC"
    r'([A-Z]{6,}(?:\s+OTC)?)',               # "EURUSD OTC"
    r'([A-Z]{6,}(?:[A-Z/]+)?)',               # "EURGBP", "EURUSD"
]
```

### **Asset Examples:**
| Message Pattern | Extracted Asset | Result |
|---------------|----------------|--------|
| `Pair: EUR/USD OTC` | `EUR/USD` | ✅ |
| `EUR/USD OTC` | `EUR/USD` | ✅ |
| `EURUSD OTC` | `EURUSD` | ✅ |
| `EURGBP` | `EURGBP` | ✅ |
| `GBP/JPY OTC` | `GBP/JPY` | ✅ |

## ⏱️ Duration Filtering Patterns

### **Time Detection (in order of specificity):**
```python
time_patterns = [
    r'⌛[️]?\s*time:\s*(\d+)\s*min',      # "⌛ time: 5 min"
    r'time:\s*(\d+)\s*min',             # "time: 5 min"
    r'(\d+)\s*min',                     # "5 min"
    r'duration:\s*(\d+)\s*min',         # "duration: 5 min"
]
```

### **Duration Examples:**
| Message Pattern | Extracted Duration | Result |
|----------------|-------------------|--------|
| `⌛ time: 5 min` | `5` | ✅ |
| `time: 5 min` | `5` | ✅ |
| `5 min` | `5` | ✅ |
| `duration: 5 min` | `5` | ✅ |
| `No time found` | `2` (default) | ⚠️ |

## 🎯 Direction Filtering Patterns

### **Direction Detection (in order of specificity):**
```python
direction_patterns = [
    r'^(Buy|Sell)\s*$',                 # "Buy" or "Sell"
    r'\b(Buy|Sell|CALL|PUT)\b',         # Any trading direction
    r'(Buy|CALL)',                           # Buy/Call
    r'(Sell|PUT)',                           # Sell/Put
    r'^([Bb])\s*$',                     # "B" for Buy
    r'^([Ss])\s*$',                     # "S" for Sell
]
```

### **Direction Examples:**
| Message Pattern | Extracted Direction | Normalized | Result |
|---------------|-------------------|------------|--------|
| `Buy` | `BUY` | `BUY` | ✅ |
| `Sell` | `SELL` | `SELL` | ✅ |
| `CALL` | `CALL` → `BUY` | `BUY` | ✅ |
| `PUT` | `PUT` → `SELL` | `SELL` | ✅ |
| `B` | `B` → `BUY` | `BUY` | ✅ |
| `S` | `S` → `SELL` | `SELL` | ✅ |

## 🔄 Complete Signal Processing

### **Two-Step Processing:**

#### **Step 1: Asset & Duration Storage**
```python
# If we got asset and duration, store it
if signal['asset'] and signal['duration']:
    last_signal['asset'] = signal['asset']
    last_signal['duration'] = signal['duration']
    log_message(f"Signal received: {signal['asset']} - {signal['duration']} min")
```

#### **Step 2: Direction & Trade Execution**
```python
# If we got direction and have stored asset/duration, place trade
if signal['direction'] and last_signal['asset'] and last_signal['duration']:
    log_message(f"Direction received: {signal['direction']}")
    
    # Place trade immediately
    await place_trade(
        asset=last_signal['asset'],
        direction=signal['direction'],
        duration=last_signal['duration']
    )
```

## 📝 Example Signal Processing

### **Complete Signal in One Message:**
```
Input: "EUR/USD OTC 5 min CALL"
Step 1: Asset="EUR/USD", Duration=5 → Store in last_signal
Step 2: Direction="CALL" → "BUY" → Place Trade
Result: Trade EUR/USD, BUY, 5 minutes
```

### **Split Signal in Two Messages:**
```
Message 1: "EUR/USD OTC 5 min"
Step 1: Asset="EUR/USD", Duration=5 → Store in last_signal
Result: Waiting for direction...

Message 2: "CALL"
Step 2: Direction="CALL" → "BUY" → Place Trade
Result: Trade EUR/USD, BUY, 5 minutes
```

## 🛡️ Smart Features

### **Duplicate Prevention:**
```python
# Check if this exact signal was just processed (within 3 seconds)
if (last_direction_signal['asset'] == last_signal['asset'] and
    last_direction_signal['direction'] == signal['direction'] and
    current_time - last_direction_signal['timestamp'] < 3):
    log_message(f"Skipping duplicate direction signal")
    return
```

### **Trade Lock:**
```python
# Prevent concurrent trade placement
async with trade_placement_lock:
    if trade_in_progress:
        log_message(f"Skipping - trade already in progress")
        return
    
    trade_in_progress = True
    try:
        # Place trade
        await place_trade(...)
    finally:
        trade_in_progress = False
```

### **Martingale Strategy:**
```python
# Keep asset until win, then advance on loss
if trade_result == 'WIN':
    current_martingale_step = 0  # Reset on win
elif trade_result == 'LOSS':
    current_martingale_step += 1  # Advance on loss
```

## 🎯 Key Benefits

1. **Flexible Input**: Handles multiple signal formats
2. **Robust Parsing**: Multiple regex patterns for reliability
3. **Smart Defaults**: 2-minute default duration
4. **Duplicate Prevention**: Avoids repeated trades
5. **Concurrent Safety**: Lock prevents race conditions
6. **Martingale Integration**: Automatic step management
7. **Real-time Processing**: Immediate trade execution

The system is designed to handle real-world trading signals with maximum reliability and flexibility!
