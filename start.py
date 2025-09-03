#!/usr/bin/env python3
"""
Startup script for the AI Profile Scraper
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Check if required Python packages are installed"""
    try:
        import fastapi
        import uvicorn
        import bs4
        import httpx
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path('.env')
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("Please copy env.example to .env and add your Gemini API key")
        return False
    
    with open(env_file, 'r') as f:
        content = f.read()
        if 'your_gemini_api_key_here' in content:
            print("⚠️  Please update your Gemini API key in .env file")
            return False
    
    print("✅ Environment configuration found")
    return True

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting backend server...")
    
    try:
        # Start the backend server without capturing output
        process = subprocess.Popen([
            sys.executable, 'main.py'
        ])
        
        # Wait longer for server to start and retry multiple times
        import requests
        max_retries = 10
        for attempt in range(max_retries):
            try:
                time.sleep(2)  # Wait 2 seconds between attempts
                response = requests.get('http://localhost:8000/api/health', timeout=5)
                if response.status_code == 200:
                    print("✅ Backend server is running on http://localhost:8000")
                    return process
            except Exception as e:
                if attempt == max_retries - 1:  # Last attempt
                    print(f"❌ Backend server failed to start after {max_retries} attempts: {e}")
                    return None
                continue  # Try again
            
        print("❌ Backend server failed to start properly")
        return None
            
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        return None

def start_frontend():
    """Start the frontend server"""
    print("🌐 Starting frontend server...")
    
    try:
        # Start a simple HTTP server for the frontend
        process = subprocess.Popen([
            sys.executable, '-m', 'http.server', '3000'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(2)
        print("✅ Frontend server is running on http://localhost:3000")
        return process
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        return None

def main():
    """Main startup function"""
    print("🤖 AI Profile Scraper - Startup")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    if not check_env_file():
        print("\nYou can still run the backend, but AI extraction will be disabled.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        print("❌ Failed to start backend. Exiting.")
        sys.exit(1)
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        print("❌ Failed to start frontend. Backend is still running.")
        print("You can access the API at: http://localhost:8000")
        print("API docs at: http://localhost:8000/docs")
    
    # Open browser
    try:
        print("\n🌐 Opening browser...")
        webbrowser.open('http://localhost:3000')
    except:
        print("Please manually open: http://localhost:3000")
    
    print("\n🎉 AI Profile Scraper is running!")
    print("\n📱 Frontend: http://localhost:3000")
    print("🔧 Backend API: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop all servers")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down servers...")
        
        if backend_process:
            backend_process.terminate()
            print("✅ Backend server stopped")
        
        if frontend_process:
            frontend_process.terminate()
            print("✅ Frontend server stopped")
        
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()
