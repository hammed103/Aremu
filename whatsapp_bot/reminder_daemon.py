#!/usr/bin/env python3
"""
24-Hour Window Reminder Daemon
Runs continuously to monitor user activity and send reminders
"""

import os
import time
import signal
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from services.whatsapp_service import WhatsAppService
from services.reminder_service import ReminderService
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Set up logging
logger = setup_logger(__name__)

class ReminderDaemon:
    def __init__(self):
        """Initialize the reminder daemon"""
        self.running = True
        self.check_interval = 300  # Check every 5 minutes
        
        # Initialize services
        whatsapp_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        whatsapp_phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        
        self.whatsapp_service = WhatsAppService(whatsapp_token, whatsapp_phone_id)
        self.reminder_service = ReminderService(self.whatsapp_service)
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("🤖 Reminder Daemon initialized")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"📡 Received signal {signum}, shutting down gracefully...")
        self.running = False

    def health_check(self) -> bool:
        """Check if all services are healthy"""
        try:
            # Test database connection
            if not self.reminder_service.connection:
                logger.error("❌ Database connection lost")
                return False
            
            # Test WhatsApp service
            if not self.whatsapp_service.whatsapp_token:
                logger.error("❌ WhatsApp token missing")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False

    def run_cycle(self):
        """Run one monitoring cycle"""
        try:
            logger.info(f"🔄 Running reminder cycle at {datetime.now()}")
            
            # Health check
            if not self.health_check():
                logger.error("❌ Health check failed, skipping cycle")
                return
            
            # Run reminder cycle
            sent_count = self.reminder_service.run_reminder_cycle()
            
            if sent_count > 0:
                logger.info(f"✅ Cycle complete: {sent_count} reminders sent")
            else:
                logger.info("✅ Cycle complete: No reminders needed")
                
        except Exception as e:
            logger.error(f"❌ Error in reminder cycle: {e}")

    def run(self):
        """Main daemon loop"""
        logger.info("🚀 Starting 24-Hour Window Reminder Daemon")
        logger.info(f"⏰ Check interval: {self.check_interval} seconds")
        
        # Create reminder log table
        self.reminder_service.create_reminder_log_table()
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                logger.info(f"🔄 Starting cycle #{cycle_count}")
                
                self.run_cycle()
                
                # Sleep until next check
                logger.info(f"😴 Sleeping for {self.check_interval} seconds...")
                
                for i in range(self.check_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                logger.info("⌨️ Keyboard interrupt received")
                break
            except Exception as e:
                logger.error(f"❌ Unexpected error in main loop: {e}")
                time.sleep(60)  # Wait a minute before retrying
        
        logger.info("👋 Reminder Daemon shutting down")

    def run_once(self):
        """Run just one cycle (for testing)"""
        logger.info("🧪 Running single reminder cycle for testing")
        self.reminder_service.create_reminder_log_table()
        self.run_cycle()


def main():
    """Main entry point"""
    daemon = ReminderDaemon()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            daemon.run_once()
            return
        elif sys.argv[1] == "health":
            if daemon.health_check():
                print("✅ All systems healthy")
                sys.exit(0)
            else:
                print("❌ Health check failed")
                sys.exit(1)
    
    # Run the daemon
    try:
        daemon.run()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
