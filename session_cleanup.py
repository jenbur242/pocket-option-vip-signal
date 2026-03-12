#!/usr/bin/env python3
"""
Automatic Session Cleanup Service
Deletes Telegram session files after 24 hours of inactivity
Stores data in both Railway and local files
"""

import os
import time
import json
import glob
from datetime import datetime, timedelta
from pathlib import Path

# Session tracking file
SESSION_TRACKER_FILE = 'session_tracker.json'
SESSION_LIFETIME_HOURS = 24

def load_session_tracker():
    """Load session tracking data"""
    try:
        if os.path.exists(SESSION_TRACKER_FILE):
            with open(SESSION_TRACKER_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading session tracker: {e}")
    
    return {
        'sessions': {},
        'last_cleanup': None
    }

def save_session_tracker(tracker_data):
    """Save session tracking data"""
    try:
        with open(SESSION_TRACKER_FILE, 'w') as f:
            json.dump(tracker_data, f, indent=2)
    except Exception as e:
        print(f"Error saving session tracker: {e}")

def register_session(session_file, phone_number=None):
    """Register a new session file"""
    tracker = load_session_tracker()
    
    tracker['sessions'][session_file] = {
        'created_at': datetime.now().isoformat(),
        'last_accessed': datetime.now().isoformat(),
        'phone_number': phone_number,
        'file_size': os.path.getsize(session_file) if os.path.exists(session_file) else 0
    }
    
    save_session_tracker(tracker)
    print(f"✅ Session registered: {session_file}")

def update_session_access(session_file):
    """Update last accessed time for a session"""
    tracker = load_session_tracker()
    
    if session_file in tracker['sessions']:
        tracker['sessions'][session_file]['last_accessed'] = datetime.now().isoformat()
        if os.path.exists(session_file):
            tracker['sessions'][session_file]['file_size'] = os.path.getsize(session_file)
        
        save_session_tracker(tracker)

def cleanup_expired_sessions():
    """Delete sessions older than 24 hours"""
    tracker = load_session_tracker()
    current_time = datetime.now()
    expired_sessions = []
    deleted_files = []
    
    for session_file, session_data in tracker['sessions'].items():
        last_accessed = datetime.fromisoformat(session_data['last_accessed'])
        
        # Check if session is expired
        if current_time - last_accessed > timedelta(hours=SESSION_LIFETIME_HOURS):
            expired_sessions.append(session_file)
            
            # Delete session files
            session_patterns = [
                session_file,
                session_file + '-journal',
                session_file.replace('.session', '*.session*')
            ]
            
            for pattern in session_patterns:
                if '*' in pattern:
                    # Handle wildcard patterns
                    matching_files = glob.glob(pattern)
                    for file_path in matching_files:
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                deleted_files.append(file_path)
                                print(f"🗑️ Deleted expired session file: {file_path}")
                            except Exception as e:
                                print(f"⚠️ Could not delete {file_path}: {e}")
                else:
                    # Handle specific files
                    if os.path.exists(pattern):
                        try:
                            os.remove(pattern)
                            deleted_files.append(pattern)
                            print(f"🗑️ Deleted expired session file: {pattern}")
                        except Exception as e:
                            print(f"⚠️ Could not delete {pattern}: {e}")
    
    # Remove expired sessions from tracker
    for session_file in expired_sessions:
        del tracker['sessions'][session_file]
    
    # Update last cleanup time
    tracker['last_cleanup'] = current_time.isoformat()
    save_session_tracker(tracker)
    
    # Store cleanup log for Railway
    cleanup_log = {
        'timestamp': current_time.isoformat(),
        'expired_sessions': expired_sessions,
        'deleted_files': deleted_files,
        'remaining_sessions': len(tracker['sessions'])
    }
    
    try:
        with open('cleanup_log.json', 'a') as f:
            f.write(json.dumps(cleanup_log) + '\n')
    except Exception as e:
        print(f"Could not write cleanup log: {e}")
    
    print(f"🧹 Cleanup completed. Deleted {len(deleted_files)} files, {len(expired_sessions)} sessions expired")
    
    return {
        'deleted_count': len(deleted_files),
        'expired_sessions': expired_sessions,
        'remaining_sessions': len(tracker['sessions'])
    }

def get_session_status():
    """Get current session status"""
    tracker = load_session_tracker()
    current_time = datetime.now()
    
    status = {
        'total_sessions': len(tracker['sessions']),
        'sessions': [],
        'last_cleanup': tracker.get('last_cleanup')
    }
    
    for session_file, session_data in tracker['sessions'].items():
        last_accessed = datetime.fromisoformat(session_data['last_accessed'])
        age_hours = (current_time - last_accessed).total_seconds() / 3600
        
        status['sessions'].append({
            'file': session_file,
            'phone_number': session_data.get('phone_number'),
            'created_at': session_data['created_at'],
            'last_accessed': session_data['last_accessed'],
            'age_hours': round(age_hours, 1),
            'expires_in_hours': round(SESSION_LIFETIME_HOURS - age_hours, 1),
            'file_exists': os.path.exists(session_file),
            'file_size': session_data.get('file_size', 0)
        })
    
    return status

def auto_cleanup_loop():
    """Run automatic cleanup every hour"""
    print("🤖 Starting automatic session cleanup service...")
    print(f"⏰ Sessions will expire after {SESSION_LIFETIME_HOURS} hours")
    
    while True:
        try:
            result = cleanup_expired_sessions()
            
            if result['deleted_count'] > 0:
                print(f"🧹 Auto-cleanup: Removed {result['deleted_count']} expired session files")
            else:
                print(f"✅ Auto-cleanup: No expired sessions. {result['remaining_sessions']} active")
            
            # Sleep for 1 hour before next cleanup
            time.sleep(3600)
            
        except KeyboardInterrupt:
            print("\n👋 Session cleanup service stopped")
            break
        except Exception as e:
            print(f"❌ Cleanup error: {e}")
            time.sleep(300)  # Wait 5 minutes before retry

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "cleanup":
            print("🧹 Running manual session cleanup...")
            cleanup_expired_sessions()
            
        elif command == "status":
            print("📊 Session Status:")
            status = get_session_status()
            
            if status['total_sessions'] == 0:
                print("   No active sessions")
            else:
                print(f"   Total sessions: {status['total_sessions']}")
                for session in status['sessions']:
                    print(f"   📁 {session['file']}")
                    print(f"      Phone: {session['phone_number']}")
                    print(f"      Age: {session['age_hours']}h (expires in {session['expires_in_hours']}h)")
                    print(f"      Size: {session['file_size']} bytes")
            
            if status['last_cleanup']:
                print(f"   Last cleanup: {status['last_cleanup']}")
        
        elif command == "register":
            if len(sys.argv) > 2:
                session_file = sys.argv[2]
                phone = sys.argv[3] if len(sys.argv) > 3 else None
                register_session(session_file, phone)
            else:
                print("Usage: python session_cleanup.py register <session_file> [phone_number]")
        
        elif command == "update":
            if len(sys.argv) > 2:
                session_file = sys.argv[2]
                update_session_access(session_file)
            else:
                print("Usage: python session_cleanup.py update <session_file>")
        
        else:
            print("Available commands:")
            print("  cleanup  - Run manual cleanup")
            print("  status   - Show session status")
            print("  register - Register new session")
            print("  update   - Update session access time")
            print("  (no args) - Start auto-cleanup service")
    
    else:
        # Start auto-cleanup service
        auto_cleanup_loop()
