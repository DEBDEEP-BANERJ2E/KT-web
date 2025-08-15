#!/usr/bin/env python3
"""
Behavioral Biometrics Authentication System
Main entry point for the application
"""

import os
import threading
import time
import uvicorn
from backend.api import app as fastapi_app
from frontend.app import create_gradio_app

def setup_environment():
    """Setup environment variables and directories"""
    # Create necessary directories
    os.makedirs("models", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("exports", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Set default environment variables if not provided
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite:///./biometrics.db"
    
    print("Environment setup complete")
    print(f"Database URL: {os.getenv('DATABASE_URL', 'sqlite:///./biometrics.db')}")
    print(f"Models directory: ./models")

def run_fastapi():
    """Run FastAPI backend server"""
    uvicorn.run(
        fastapi_app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )

def run_gradio():
    """Run Gradio frontend server"""
    time.sleep(2)  # Wait for FastAPI to start
    gradio_app = create_gradio_app()
    gradio_app.launch(
        server_name="0.0.0.0",
        server_port=5000,
        share=False,
        debug=False,
        show_api=False
    )

if __name__ == "__main__":
    # Setup environment
    setup_environment()
    
    # Start FastAPI in background thread
    api_thread = threading.Thread(target=run_fastapi, daemon=True)
    api_thread.start()
    
    print("FastAPI server starting on port 8000...")
    print("Gradio interface will start on port 5000...")
    
    # Start Gradio in main thread
    run_gradio()
