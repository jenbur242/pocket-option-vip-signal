import os
from datetime import datetime

# Generate unique session name
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
new_session = f'session_pocket_option_vip_{timestamp}'

# Update main.py
main_file = 'telegram/main.py'
try:
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update session name
    content = content.replace(
        "client = TelegramClient('session_pocket_option_vip', API_ID, API_HASH)",
        f"client = TelegramClient('{new_session}', API_ID, API_HASH)"
    )
    
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated main.py with new session: {new_session}")
    print("Session will be created when bot starts first time")
    
except Exception as e:
    print(f"Error updating main.py: {e}")
