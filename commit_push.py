print("Committing current state with working session...")

import subprocess
import sys

try:
    # Add all changes
    subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
    
    # Commit with clear message
    result = subprocess.run(['git', 'commit', '-m', 'Fix database lock - use existing working session'], 
                         capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Committed successfully")
        
        # Push to GitHub
        push_result = subprocess.run(['git', 'push', 'origin', 'main'], 
                               capture_output=True, text=True)
        
        if push_result.returncode == 0:
            print("✅ Pushed to GitHub successfully!")
            print("🚀 Ready for Railway deployment!")
        else:
            print("❌ Push failed:", push_result.stderr)
    else:
        print("❌ Commit failed:", result.stderr)
        
except Exception as e:
    print(f"❌ Error: {e}")
