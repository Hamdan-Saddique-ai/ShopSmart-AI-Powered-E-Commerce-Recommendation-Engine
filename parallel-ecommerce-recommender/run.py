#!/usr/bin/env python3
import subprocess
import sys
import os
import time
import webbrowser
from threading import Thread

def check_requirements():
    """Check and install required packages"""
    print("Checking requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def generate_dataset():
    """Generate synthetic dataset"""
    print("Generating synthetic dataset...")
    subprocess.check_call([sys.executable, "dataset/generate_data.py"])

def start_backend():
    """Start FastAPI backend server"""
    print("Starting backend server on http://localhost:8000")
    os.environ["PYTHONPATH"] = os.getcwd()
    subprocess.run([sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])

def start_frontend():
    """Start frontend server"""
    print("Starting frontend server on http://localhost:3000")
    
    # Simple HTTP server for frontend
    os.chdir("frontend")
    subprocess.run([sys.executable, "-m", "http.server", "3000"])
    
def main():
    print("=" * 60)
    print("PARALLEL E-COMMERCE RECOMMENDATION SYSTEM")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("Error: Python 3.7+ required")
        sys.exit(1)
    
    # Install requirements
    check_requirements()
    
    # Generate dataset if needed
    if not os.path.exists("ecommerce.db"):
        generate_dataset()
    
    # Start servers in threads
    print("\nStarting servers...")
    
    # Start backend in a thread
    backend_thread = Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Wait for backend to start
    time.sleep(3)
    
    # Open browser
    webbrowser.open("http://localhost:3000")
    
    print("\n" + "=" * 60)
    print("SYSTEM READY!")
    print("=" * 60)
    print("\nAccess Points:")
    print("  - Frontend: http://localhost:3000")
    print("  - Backend API: http://localhost:8000")
    print("  - API Docs: http://localhost:8000/docs")
    print("\nTest Credentials:")
    print("  - Username: Any registered user")
    print("  - Or register a new account")
    print("\nPress Ctrl+C to stop the servers")
    print("=" * 60)
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()