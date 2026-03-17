#!/usr/bin/env python3
"""
Startup check for Railway deployment
"""

import sys
import os
import asyncio
from datetime import datetime

def log_message(message: str):
    """Log with timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[STARTUP] {timestamp} - {message}")

async def test_imports():
    """Test all required imports"""
    log_message("Testing imports...")
    
    try:
        import fastapi
        log_message(f"[OK] FastAPI {fastapi.__version__}")
    except ImportError as e:
        log_message(f"[ERROR] FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        log_message(f"[OK] Uvicorn available")
    except ImportError as e:
        log_message(f"[ERROR] Uvicorn import failed: {e}")
        return False
    
    try:
        from fastapi.responses import JSONResponse, FileResponse
        log_message("[OK] FastAPI responses available")
    except ImportError as e:
        log_message(f"[ERROR] FastAPI responses import failed: {e}")
        return False
    
    try:
        from fastapi.middleware.cors import CORSMiddleware
        log_message("[OK] CORS middleware available")
    except ImportError as e:
        log_message(f"[ERROR] CORS middleware import failed: {e}")
        return False
    
    return True

async def test_app_creation():
    """Test app creation"""
    log_message("Testing app creation...")
    
    try:
        from app import app
        log_message("[OK] App imported successfully")
        
        # Test basic endpoints
        log_message("Testing endpoints...")
        
        # Test health endpoint
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        response = client.get("/health")
        if response.status_code == 200:
            log_message("[OK] Health endpoint working")
        else:
            log_message(f"[ERROR] Health endpoint failed: {response.status_code}")
            return False
        
        # Test API endpoint
        response = client.get("/api")
        if response.status_code == 200:
            log_message("[OK] API endpoint working")
        else:
            log_message(f"[ERROR] API endpoint failed: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        log_message(f"[ERROR] App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_environment():
    """Check environment variables"""
    log_message("Checking environment...")
    
    # Check Python version
    log_message(f"Python version: {sys.version}")
    
    # Check working directory
    log_message(f"Working directory: {os.getcwd()}")
    
    # Check files
    files_to_check = ["app.py", "requirements.txt", "dashboard.html"]
    for file in files_to_check:
        if os.path.exists(file):
            size = os.path.getsize(file)
            log_message(f"[OK] {file} exists ({size} bytes)")
        else:
            log_message(f"[ERROR] {file} missing")
    
    # Check environment variables
    env_vars = ["PORT", "RAILWAY_ENVIRONMENT", "IS_DEMO"]
    for var in env_vars:
        value = os.getenv(var)
        if value:
            log_message(f"[OK] {var}={value}")
        else:
            log_message(f"[WARNING] {var} not set")

async def main():
    """Main startup check"""
    log_message("=== Railway Startup Check ===")
    
    # Check environment
    check_environment()
    
    # Test imports
    if not await test_imports():
        log_message("[ERROR] Import tests failed")
        return False
    
    # Test app creation
    if not await test_app_creation():
        log_message("[ERROR] App creation tests failed")
        return False
    
    log_message("[OK] All startup checks passed!")
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if success:
            log_message("[OK] Ready to start app.py")
            sys.exit(0)
        else:
            log_message("[ERROR] Startup checks failed")
            sys.exit(1)
    except Exception as e:
        log_message(f"[ERROR] Startup check error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
