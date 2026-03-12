#!/usr/bin/env python3
"""
Session cleanup module for Railway deployment
Handles session management and cleanup operations
"""
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Session storage file
SESSION_FILE = 'sessions.json'
SESSION_TIMEOUT = 3600  # 1 hour in seconds

def register_session(session_id: str, user_data: Dict[str, Any] = None) -> bool:
    """Register a new session"""
    try:
        sessions = load_sessions()
        
        sessions[session_id] = {
            'created_at': datetime.now().isoformat(),
            'last_access': datetime.now().isoformat(),
            'user_data': user_data or {},
            'active': True
        }
        
        save_sessions(sessions)
        return True
    except Exception as e:
        print(f"Error registering session: {e}")
        return False

def update_session_access(session_id: str) -> bool:
    """Update last access time for a session"""
    try:
        sessions = load_sessions()
        
        if session_id in sessions:
            sessions[session_id]['last_access'] = datetime.now().isoformat()
            sessions[session_id]['active'] = True
            save_sessions(sessions)
            return True
        else:
            return False
    except Exception as e:
        print(f"Error updating session access: {e}")
        return False

def cleanup_expired_sessions() -> int:
    """Clean up expired sessions and return count of cleaned sessions"""
    try:
        sessions = load_sessions()
        current_time = datetime.now()
        cleaned_count = 0
        
        expired_sessions = []
        for session_id, session_data in sessions.items():
            last_access = datetime.fromisoformat(session_data['last_access'])
            
            # Check if session is expired (older than SESSION_TIMEOUT)
            if current_time - last_access > timedelta(seconds=SESSION_TIMEOUT):
                expired_sessions.append(session_id)
        
        # Remove expired sessions
        for session_id in expired_sessions:
            del sessions[session_id]
            cleaned_count += 1
        
        save_sessions(sessions)
        return cleaned_count
    except Exception as e:
        print(f"Error cleaning up sessions: {e}")
        return 0

def get_session_status(session_id: str) -> Optional[Dict[str, Any]]:
    """Get status of a specific session"""
    try:
        sessions = load_sessions()
        
        if session_id in sessions:
            session_data = sessions[session_id].copy()
            
            # Check if session is expired
            last_access = datetime.fromisoformat(session_data['last_access'])
            current_time = datetime.now()
            
            is_expired = current_time - last_access > timedelta(seconds=SESSION_TIMEOUT)
            
            return {
                'session_id': session_id,
                'created_at': session_data['created_at'],
                'last_access': session_data['last_access'],
                'active': session_data['active'] and not is_expired,
                'expired': is_expired,
                'user_data': session_data.get('user_data', {})
            }
        else:
            return None
    except Exception as e:
        print(f"Error getting session status: {e}")
        return None

def get_all_sessions() -> Dict[str, Any]:
    """Get all active sessions"""
    try:
        sessions = load_sessions()
        current_time = datetime.now()
        active_sessions = {}
        
        for session_id, session_data in sessions.items():
            last_access = datetime.fromisoformat(session_data['last_access'])
            
            # Only include non-expired sessions
            if current_time - last_access <= timedelta(seconds=SESSION_TIMEOUT):
                active_sessions[session_id] = {
                    'created_at': session_data['created_at'],
                    'last_access': session_data['last_access'],
                    'active': session_data['active'],
                    'user_data': session_data.get('user_data', {})
                }
        
        return active_sessions
    except Exception as e:
        print(f"Error getting all sessions: {e}")
        return {}

def invalidate_session(session_id: str) -> bool:
    """Invalidate a specific session"""
    try:
        sessions = load_sessions()
        
        if session_id in sessions:
            sessions[session_id]['active'] = False
            save_sessions(sessions)
            return True
        else:
            return False
    except Exception as e:
        print(f"Error invalidating session: {e}")
        return False

def load_sessions() -> Dict[str, Any]:
    """Load sessions from file"""
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading sessions: {e}")
        return {}

def save_sessions(sessions: Dict[str, Any]) -> bool:
    """Save sessions to file"""
    try:
        with open(SESSION_FILE, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, indent=2, default=str)
        return True
    except Exception as e:
        print(f"Error saving sessions: {e}")
        return False

def get_session_stats() -> Dict[str, Any]:
    """Get session statistics"""
    try:
        sessions = load_sessions()
        current_time = datetime.now()
        
        total_sessions = len(sessions)
        active_sessions = 0
        expired_sessions = 0
        
        for session_data in sessions.values():
            last_access = datetime.fromisoformat(session_data['last_access'])
            
            if current_time - last_access > timedelta(seconds=SESSION_TIMEOUT):
                expired_sessions += 1
            elif session_data.get('active', True):
                active_sessions += 1
        
        return {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'expired_sessions': expired_sessions,
            'session_timeout': SESSION_TIMEOUT,
            'session_file': SESSION_FILE,
            'last_cleanup': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error getting session stats: {e}")
        return {
            'total_sessions': 0,
            'active_sessions': 0,
            'expired_sessions': 0,
            'session_timeout': SESSION_TIMEOUT,
            'session_file': SESSION_FILE,
            'error': str(e)
        }

# Auto-cleanup function (can be called periodically)
def auto_cleanup() -> Dict[str, Any]:
    """Perform automatic cleanup and return results"""
    try:
        cleaned_count = cleanup_expired_sessions()
        stats = get_session_stats()
        
        return {
            'cleaned_sessions': cleaned_count,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'cleaned_sessions': 0,
            'stats': {},
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }

if __name__ == "__main__":
    # Test the session cleanup module
    print("Testing session cleanup module...")
    
    # Test registration
    test_session_id = "test_session_123"
    user_data = {"user": "test_user", "ip": "127.0.0.1"}
    
    if register_session(test_session_id, user_data):
        print("SUCCESS: Session registered successfully")
    else:
        print("ERROR: Session registration failed")
    
    # Test status
    status = get_session_status(test_session_id)
    if status:
        print(f"SUCCESS: Session status: {status['active']}")
    else:
        print("ERROR: Could not get session status")
    
    # Test stats
    stats = get_session_stats()
    print(f"SUCCESS: Session stats: {stats}")
    
    # Test cleanup
    cleaned = cleanup_expired_sessions()
    print(f"SUCCESS: Cleaned {cleaned} expired sessions")
    
    print("Session cleanup module test completed!")
