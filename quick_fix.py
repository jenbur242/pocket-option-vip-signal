import os
from datetime import datetime

# Create completely new session name
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
new_session = f'session_pocket_option_vip_{timestamp}'

# Simple direct update of main.py
main_file = 'telegram/main.py'
try:
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace all session references
    content = content.replace(
        "session_pocket_option_vip_20260310_155330", 
        new_session
    )
    
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Session updated to: {new_session}")
    
except Exception as e:
    print(f"Error: {e}")
