import os
from datetime import datetime

# Generate new unique session name
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
new_session = f'session_pocket_option_vip_{timestamp}'

print(f"Creating new session name: {new_session}")

# Update main.py with new session
main_file = 'telegram/main.py'
try:
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the session name
    lines = content.split('\n')
    updated_lines = []
    
    for line in lines:
        if "client = TelegramClient('" in line and "API_ID, API_HASH)" in line:
            # Update the session name
            updated_line = line.split("'")[0] + f"'{new_session}', API_ID, API_HASH)"
            updated_lines.append(updated_line)
        else:
            updated_lines.append(line)
    
    # Write back to main.py
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(updated_lines))
    
    print(f"✅ Updated main.py with session: {new_session}")
    print("🚀 Ready to push to GitHub!")
    
except Exception as e:
    print(f"❌ Error updating main.py: {e}")
