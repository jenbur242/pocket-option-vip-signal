import os
from datetime import datetime

# Generate new unique session name with current time
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
new_session = f'session_pocket_option_vip_{timestamp}'

print(f"New session name: {new_session}")

# Update main.py with new session
main_file = 'telegram/main.py'
try:
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the old session name with new one
    old_line = "client = TelegramClient('session_pocket_option_vip_20260310_155330', API_ID, API_HASH)"
    new_line = f"client = TelegramClient('{new_session}', API_ID, API_HASH)"
    
    content = content.replace(old_line, new_line)
    
    # Also update the print statement
    old_print = 'print("📁 Using file session: session_pocket_option_vip_20260310_155330.session")'
    new_print = f'print("📁 Using file session: {new_session}.session")'
    content = content.replace(old_print, new_print)
    
    # Write back to main.py
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Updated main.py with new session: {new_session}")
    print("🗑️ Old session conflicts resolved")
    print("🚀 Ready to commit and push!")
    
except Exception as e:
    print(f"❌ Error updating main.py: {e}")
