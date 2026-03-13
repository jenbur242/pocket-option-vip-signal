#!/usr/bin/env python3
"""
Test script to verify Railway deployment setup
"""

import os
import sys
from pathlib import Path

def test_files_exist():
    """Check if all required files exist"""
    required_files = [
        'app.py',
        'Procfile', 
        'railway.json',
        'requirements.txt',
        'main.py',
        '.env.example',
        'RAILWAY_DEPLOYMENT.md'
    ]
    
    print("Checking required files...")
    all_exist = True
    
    for file in required_files:
        if os.path.exists(file):
            print(f"[OK] {file}")
        else:
            print(f"[ERROR] {file} - MISSING")
            all_exist = False
    
    return all_exist

def test_requirements():
    """Check requirements.txt"""
    print("\nChecking requirements.txt...")
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        required_packages = ['fastapi', 'uvicorn', 'telethon', 'python-dotenv']
        
        for package in required_packages:
            if package in requirements:
                print(f"[OK] {package} found")
            else:
                print(f"[ERROR] {package} missing")
                
    except FileNotFoundError:
        print("[ERROR] requirements.txt not found")

def test_procfile():
    """Check Procfile"""
    print("\nChecking Procfile...")
    
    try:
        with open('Procfile', 'r') as f:
            procfile = f.read().strip()
        
        if 'web: python app.py' in procfile:
            print("[OK] Procfile correctly configured")
        else:
            print("[ERROR] Procfile not configured correctly")
            print(f"Current content: {procfile}")
            
    except FileNotFoundError:
        print("[ERROR] Procfile not found")

def test_app_py():
    """Check app.py"""
    print("\nChecking app.py...")
    
    try:
        with open('app.py', 'r') as f:
            app_content = f.read()
        
        required_elements = ['FastAPI', 'app.get', 'uvicorn.run', 'PORT']
        
        for element in required_elements:
            if element in app_content:
                print(f"[OK] {element} found")
            else:
                print(f"[ERROR] {element} missing")
                
    except FileNotFoundError:
        print("[ERROR] app.py not found")

def test_main_py():
    """Check main.py"""
    print("\nChecking main.py...")
    
    try:
        with open('main.py', 'r') as f:
            main_content = f.read()
        
        required_elements = ['async def main', 'TelegramClient', 'place_trade']
        
        for element in required_elements:
            if element in main_content:
                print(f"[OK] {element} found")
            else:
                print(f"[ERROR] {element} missing")
                
    except FileNotFoundError:
        print("[ERROR] main.py not found")

def test_directories():
    """Check if directories can be created"""
    print("\nTesting directory creation...")
    
    test_dirs = ['/tmp/logs', '/tmp/csv', 'telegram/logs', 'telegram/trades']
    
    for dir_path in test_dirs:
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print(f"[OK] {dir_path} - OK")
        except Exception as e:
            print(f"[ERROR] {dir_path} - ERROR: {e}")

def main():
    """Run all tests"""
    print("Railway Deployment Setup Test")
    print("=" * 40)
    
    # Run all tests
    tests = [
        test_files_exist,
        test_requirements,
        test_procfile,
        test_app_py,
        test_main_py,
        test_directories
    ]
    
    for test in tests:
        test()
    
    print("\n" + "=" * 40)
    print("Setup test completed!")
    print("\nNext steps:")
    print("1. Commit and push to GitHub")
    print("2. Connect repository to Railway")
    print("3. Configure environment variables")
    print("4. Deploy!")

if __name__ == "__main__":
    main()
