#!/usr/bin/env python3
"""
Simplified main entry point for Behavioral Biometrics System
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from main import setup_environment
from backend.api import app as fastapi_app
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main entry point"""
    logger.info("🔐 Starting Behavioral Biometrics Authentication System")
    
    # Setup environment
    setup_environment()
    logger.info("✅ Environment setup completed")
    
    # Start FastAPI server
    logger.info("🚀 Starting FastAPI server on port 5000...")
    uvicorn.run(
        fastapi_app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )

if __name__ == "__main__":
    main()