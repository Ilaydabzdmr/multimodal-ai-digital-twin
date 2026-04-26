#!/usr/bin/env python3
"""
Health Coach FastAPI Server - Mac/Linux Startup Script
======================================================

This script starts the Health Coach application on Mac and Linux systems.
It performs virtual environment checks and automatically starts the server.

PURPOSE:
- Easily start Health Coach application on Mac/Linux
- Perform virtual environment check
- Provide automatic server startup
- Ensure cross-platform compatibility

REASON FOR CREATION:
- Easy startup on non-Windows systems
- Virtual environment management
- Automatic dependency control
- Improve user experience

USAGE:
- python start_server.py
- chmod +x start_server.py && ./start_server.py

FEATURES:
- Virtual environment check
- Automatic dependency installation
- User notification on errors
- Easy startup and shutdown
"""

import os
import sys
import subprocess
from pathlib import Path

def check_virtual_env():
    """Checks virtual environment"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def activate_virtual_env():
    """Activates virtual environment"""
    venv_path = Path(".venv")
    if not venv_path.exists():
        print("❌ Virtual environment not found!")
        print("Recommended commands:")
        print("  python -m venv .venv")
        print("  source .venv/bin/activate")
        return False
    
    # Activate virtual environment
    activate_script = venv_path / "bin" / "activate"
    if activate_script.exists():
        return True
    return False

def install_dependencies():
    """Installs required dependencies"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Dependency installation error: {e}")
        return False

def start_server():
    """Starts FastAPI server"""
    try:
        print("🚀 Starting FastAPI server...")
        print("📍 Address: http://127.0.0.1:8000")
        print("📚 Documentation: http://127.0.0.1:8000/docs")
        print("⏹️  Press Ctrl+C to stop")
        print("=" * 50)
        
        # Start server with Uvicorn
        subprocess.run([
            sys.executable, "-c", 
            "import uvicorn; uvicorn.run('main:app', host='127.0.0.1', port=8000)"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
    except Exception as e:
        print(f"❌ Server startup error: {e}")

def main():
    """Main function"""
    print("🏥 Health Coach FastAPI Server")
    print("=" * 50)
    
    # Virtual environment check
    if not check_virtual_env():
        print("⚠️  Virtual environment is not active!")
        if not activate_virtual_env():
            print("❌ Could not activate virtual environment!")
            sys.exit(1)
    
    # Dependency check
    print("📦 Checking dependencies...")
    if not install_dependencies():
        print("❌ Dependency installation failed!")
        sys.exit(1)
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()