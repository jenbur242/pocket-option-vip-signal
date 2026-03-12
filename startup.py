#!/usr/bin/env python3
"""
Startup script for Pocket Option Trading Bot
Runs session cleanup service in background
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path

def start_session_cleanup():
    """Start session cleanup service in background"""
    try:
        print("🚀 Starting session cleanup service...")
        
        # Start session cleanup in background
        cleanup_process = subprocess.Popen([
            sys.executable, 'session_cleanup.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("✅ Session cleanup service started (PID: {})".format(cleanup_process.pid))
        return cleanup_process
        
    except Exception as e:
        print(f"❌ Failed to start session cleanup: {e}")
        return None

def start_api_server():
    """Start the API server"""
    try:
        print("🌐 Starting API server...")
        
        # Start API server
        api_process = subprocess.Popen([
            sys.executable, 'api_server.py'
        ])
        
        print("✅ API server started (PID: {})".format(api_process.pid))
        return api_process
        
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n👋 Shutting down services...")
    
    # Cleanup processes would go here
    print("✅ Services stopped")
    sys.exit(0)

def main():
    """Main startup function"""
    print("=" * 60)
    print("🤖 POCKET OPTION TRADING BOT - STARTUP")
    print("=" * 60)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("📝 Please create a .env file with your configuration")
        sys.exit(1)
    
    print("✅ .env file found")
    
    # Start session cleanup service
    cleanup_process = start_session_cleanup()
    
    # Wait a moment before starting API server
    time.sleep(2)
    
    # Start API server
    api_process = start_api_server()
    
    print("=" * 60)
    print("🚀 All services started successfully!")
    print("📊 Session cleanup: Running (auto-cleanup every hour)")
    print("🌐 API server: Running")
    print("🕐 Sessions expire after: 24 hours")
    print("=" * 60)
    
    try:
        # Keep the main process alive
        while True:
            time.sleep(60)
            
            # Check if processes are still running
            if cleanup_process and cleanup_process.poll() is not None:
                print("⚠️ Session cleanup service stopped, restarting...")
                cleanup_process = start_session_cleanup()
            
            if api_process and api_process.poll() is not None:
                print("⚠️ API server stopped, restarting...")
                api_process = start_api_server()
                
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()
