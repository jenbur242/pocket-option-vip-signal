#!/usr/bin/env python3
"""
Complete Railway-Ready Startup Script
Includes session monitoring and automatic renewal
"""

import os
import sys
import time
import asyncio
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def start_session_monitor():
    """Start session monitoring in background"""
    try:
        import subprocess
        print("🔍 Starting session monitoring service...")
        
        # Start session monitor in background
        monitor_process = subprocess.Popen([
            sys.executable, 'session_monitor.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"✅ Session monitor started (PID: {monitor_process.pid})")
        return monitor_process
        
    except Exception as e:
        print(f"❌ Failed to start session monitor: {e}")
        return None

def start_api_server():
    """Start API server"""
    try:
        import subprocess
        print("🌐 Starting API server...")
        
        # Start API server
        api_process = subprocess.Popen([
            sys.executable, 'api_server.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"✅ API server started (PID: {api_process.pid})")
        return api_process
        
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None

def check_string_session():
    """Check if string session is configured"""
    string_session = os.getenv('TELEGRAM_STRING_SESSION')
    
    if string_session and string_session.strip():
        print("✅ String session found - Railway ready!")
        print(f"📏 Session length: {len(string_session)} characters")
        return True
    else:
        print("❌ No string session found")
        print("💡 Run: python railway_session_manager.py")
        print("💡 Then: python railway_otp_handler.py <OTP_CODE>")
        return False

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n👋 Shutting down services...")
    
    # Here you would clean up processes
    sys.exit(0)

def main():
    """Main startup function"""
    print("=" * 60)
    print("🚀 POCKET OPTION - RAILWAY STARTUP")
    print("=" * 60)
    
    # Register signal handlers
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check prerequisites
    print("🔍 Checking prerequisites...")
    
    # Check string session
    if not check_string_session():
        print("\n❌ SETUP INCOMPLETE")
        print("=" * 60)
        sys.exit(1)
    
    # Check essential environment variables
    required_vars = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_PHONE']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    print("✅ All prerequisites met!")
    
    # Start services
    processes = []
    
    # Start session monitor
    monitor_process = start_session_monitor()
    if monitor_process:
        processes.append(monitor_process)
    
    # Wait a moment before starting API server
    time.sleep(2)
    
    # Start API server
    api_process = start_api_server()
    if api_process:
        processes.append(api_process)
    
    print("\n" + "=" * 60)
    print("🎉 ALL SERVICES STARTED")
    print("=" * 60)
    print("🔍 Session Monitor: Running (checks every 5 minutes)")
    print("🌐 API Server: Running (http://localhost:5000)")
    print("🤖 Bot: Railway-ready with string session")
    print("🔄 Auto-renewal: Enabled")
    print("=" * 60)
    print("\n💡 Features:")
    print("   • Continuous session monitoring")
    print("   • Automatic expiration detection")
    print("   • Frontend OTP renewal prompts")
    print("   • Backend session management")
    print("   • Railway deployment ready")
    print("\n📋 Monitor Status:")
    print("   • Session validity checked every 5 minutes")
    print("   • Automatic renewal on expiration")
    print("   • Frontend alerts for expired sessions")
    print("   • Browser storage integration")
    print("\n🛑 Press Ctrl+C to stop all services")
    
    try:
        # Keep main process alive and monitor subprocesses
        while True:
            time.sleep(10)
            
            # Check if processes are still running
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    print(f"⚠️ Process {i} stopped, restarting...")
                    
                    if i == 0:  # Session monitor
                        processes[i] = start_session_monitor()
                    elif i == 1:  # API server
                        processes[i] = start_api_server()
                    
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        print(f"❌ Startup error: {e}")

if __name__ == "__main__":
    main()
