#!/usr/bin/env python3
"""
Production server runner for Behavioral Biometrics System
Handles both FastAPI backend and Gradio frontend
"""

import os
import sys
import signal
import threading
import time
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import setup_environment, run_fastapi, run_gradio

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('biometrics_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class BiometricsServer:
    """Production server manager for the Behavioral Biometrics System"""
    
    def __init__(self):
        self.fastapi_thread = None
        self.gradio_thread = None
        self.running = False
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """Start the biometrics server"""
        logger.info("🚀 Starting Behavioral Biometrics Authentication System")
        
        # Setup environment
        try:
            setup_environment()
            logger.info("✅ Environment setup completed")
        except Exception as e:
            logger.error(f"❌ Environment setup failed: {e}")
            return False
        
        # Validate configuration
        self.validate_configuration()
        
        # Start FastAPI backend
        logger.info("🔧 Starting FastAPI backend server...")
        self.fastapi_thread = threading.Thread(
            target=self.run_fastapi_with_error_handling,
            daemon=True,
            name="FastAPI-Server"
        )
        self.fastapi_thread.start()
        
        # Wait for FastAPI to start
        time.sleep(3)
        logger.info("✅ FastAPI backend started on port 8000")
        
        # Start Gradio frontend
        logger.info("🎨 Starting Gradio frontend interface...")
        self.gradio_thread = threading.Thread(
            target=self.run_gradio_with_error_handling,
            daemon=True,
            name="Gradio-Frontend"
        )
        self.gradio_thread.start()
        
        # Wait for Gradio to start
        time.sleep(2)
        logger.info("✅ Gradio frontend started on port 5000")
        
        self.running = True
        
        # Display startup information
        self.display_startup_info()
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.stop()
        
        return True
    
    def run_fastapi_with_error_handling(self):
        """Run FastAPI with error handling"""
        try:
            run_fastapi()
        except Exception as e:
            logger.error(f"❌ FastAPI server error: {e}")
            self.running = False
    
    def run_gradio_with_error_handling(self):
        """Run Gradio with error handling"""
        try:
            run_gradio()
        except Exception as e:
            logger.error(f"❌ Gradio server error: {e}")
            self.running = False
    
    def validate_configuration(self):
        """Validate system configuration"""
        logger.info("🔍 Validating system configuration...")
        
        # Check required environment variables
        required_vars = []
        optional_vars = [
            'TYPINGDNA_API_KEY',
            'TYPINGDNA_API_SECRET',
            'EMAIL_USER',
            'EMAIL_PASSWORD',
            'WEBHOOK_URL',
            'GOOGLE_DRIVE_FOLDER_ID'
        ]
        
        # Log configuration status
        for var in optional_vars:
            value = os.getenv(var)
            if value:
                logger.info(f"✅ {var}: Configured")
            else:
                logger.warning(f"⚠️  {var}: Not configured (optional)")
        
        # Check directory structure
        directories = ['models', 'data', 'exports', 'logs', 'static']
        for directory in directories:
            if os.path.exists(directory):
                logger.info(f"✅ Directory {directory}: OK")
            else:
                logger.warning(f"⚠️  Directory {directory}: Missing (will be created)")
        
        logger.info("✅ Configuration validation completed")
    
    def display_startup_info(self):
        """Display startup information"""
        print("\n" + "="*60)
        print("🔐 BEHAVIORAL BIOMETRICS AUTHENTICATION SYSTEM")
        print("="*60)
        print()
        print("🌐 Server Information:")
        print(f"   FastAPI Backend:  http://localhost:8000")
        print(f"   Gradio Frontend:  http://localhost:5000")
        print(f"   Started at:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("📊 Available Features:")
        print("   • Real-time typing dynamics analysis")
        print("   • Behavioral biometric authentication")
        print("   • Continuous authentication monitoring")
        print("   • Admin dashboard and analytics")
        print("   • Data export and management")
        print("   • Mobile QR code access")
        print()
        print("🔧 External Services:")
        print(f"   • TypingDNA Integration: {'✅ Enabled' if os.getenv('TYPINGDNA_API_KEY') else '❌ Disabled'}")
        print(f"   • Email Notifications: {'✅ Enabled' if os.getenv('EMAIL_USER') else '❌ Disabled'}")
        print(f"   • Webhook Alerts:      {'✅ Enabled' if os.getenv('WEBHOOK_URL') else '❌ Disabled'}")
        print(f"   • Google Drive Sync:   {'✅ Enabled' if os.getenv('GOOGLE_DRIVE_ENABLED') == 'true' else '❌ Disabled'}")
        print()
        print("📝 API Documentation:")
        print("   • Swagger UI:         http://localhost:8000/docs")
        print("   • ReDoc:              http://localhost:8000/redoc")
        print()
        print("🚀 Ready for authentication requests!")
        print("   Press Ctrl+C to stop the server")
        print("="*60)
        print()
    
    def stop(self):
        """Stop the server"""
        logger.info("🛑 Stopping Behavioral Biometrics System...")
        self.running = False
        
        # Give threads time to clean up
        if self.fastapi_thread and self.fastapi_thread.is_alive():
            logger.info("⏳ Waiting for FastAPI server to stop...")
            time.sleep(1)
        
        if self.gradio_thread and self.gradio_thread.is_alive():
            logger.info("⏳ Waiting for Gradio frontend to stop...")
            time.sleep(1)
        
        logger.info("✅ Server stopped successfully")
    
    def health_check(self):
        """Perform system health check"""
        logger.info("🏥 Performing system health check...")
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'fastapi_running': self.fastapi_thread and self.fastapi_thread.is_alive(),
            'gradio_running': self.gradio_thread and self.gradio_thread.is_alive(),
            'overall_status': self.running
        }
        
        logger.info(f"Health check result: {health_status}")
        return health_status


def main():
    """Main entry point"""
    print("🔐 Behavioral Biometrics Authentication System")
    print("Starting server...")
    
    # Create and start server
    server = BiometricsServer()
    
    try:
        success = server.start()
        if not success:
            logger.error("❌ Failed to start server")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
