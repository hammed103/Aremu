#!/usr/bin/env python3
"""
Railway deployment startup script
Starts all services including automated cleanup
"""

import os
import sys
import time
import threading
import signal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.automated_cleanup_service import AutomatedCleanupService
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Global variables for services
cleanup_service = None
cleanup_thread = None
running = True


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global running, cleanup_service
    
    logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
    running = False
    
    if cleanup_service:
        cleanup_service.stop()
    
    logger.info("👋 Shutdown complete")
    sys.exit(0)


def start_cleanup_service():
    """Start the automated cleanup service"""
    global cleanup_service, cleanup_thread
    
    try:
        logger.info("🧹 Initializing automated cleanup service...")
        cleanup_service = AutomatedCleanupService()
        
        # Run initial cleanup
        logger.info("🧹 Running initial cleanup...")
        cleanup_service.run_full_cleanup()
        
        # Start automated cleanup every 5 hours
        cleanup_thread = cleanup_service.start_automated_cleanup(interval_hours=5)
        logger.info("✅ Automated cleanup service started successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to start cleanup service: {e}")
        return False


def start_main_app():
    """Start the main Flask application"""
    try:
        logger.info("🚀 Starting main Flask application...")
        
        # Import and run the main app
        from app import app
        
        port = int(os.environ.get("PORT", 5001))
        
        # Set production environment
        os.environ["FLASK_ENV"] = "production"
        
        logger.info(f"🌐 Starting Flask app on port {port}")
        app.run(host="0.0.0.0", port=port, debug=False)
        
    except Exception as e:
        logger.error(f"❌ Failed to start main app: {e}")
        return False


def main():
    """Main function for Railway deployment"""
    global running
    
    logger.info("🚀 Starting Aremu.ai Railway Deployment")
    logger.info("=" * 50)
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start cleanup service in background
        cleanup_success = start_cleanup_service()
        
        if not cleanup_success:
            logger.warning("⚠️ Cleanup service failed to start, continuing without it")
        
        # Start main application (this will block)
        logger.info("🚀 Starting main application...")
        start_main_app()
        
    except KeyboardInterrupt:
        logger.info("🛑 Received keyboard interrupt")
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        logger.error(f"❌ Fatal error in Railway startup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
