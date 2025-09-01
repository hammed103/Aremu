#!/usr/bin/env python3
"""
Baileys WhatsApp Scraper - Python Wrapper
Integrates the Node.js Baileys WhatsApp scraper with the Python scraper service
"""

import os
import sys
import subprocess
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directories to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from database.config import get_database_url
except ImportError:
    def get_database_url():
        return "postgresql://postgres.upnvhpgaljazlsoryfgj:prAlkIpbQDqOZtOj@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

logger = logging.getLogger(__name__)


class BaileysWhatsAppScraper:
    """Python wrapper for the Baileys WhatsApp scraper"""
    
    def __init__(self):
        """Initialize the Baileys scraper wrapper"""
        self.baileys_dir = os.path.join(os.path.dirname(__file__), "baileys-client")
        self.process = None
        self.is_running = False
        self.database_url = get_database_url()
        
        # Set environment variables for the Node.js process
        self.env = os.environ.copy()
        self.env['DATABASE_URL'] = self.database_url
        
        logger.info("🔧 Baileys WhatsApp scraper wrapper initialized")
    
    def check_dependencies(self) -> bool:
        """Check if Node.js and required packages are available"""
        try:
            # Check Node.js
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                logger.error("❌ Node.js not found")
                return False
            
            logger.info(f"✅ Node.js found: {result.stdout.strip()}")
            
            # Check if baileys-client directory exists
            if not os.path.exists(self.baileys_dir):
                logger.error(f"❌ Baileys client directory not found: {self.baileys_dir}")
                return False
            
            # Check if package.json exists
            package_json = os.path.join(self.baileys_dir, "package.json")
            if not os.path.exists(package_json):
                logger.error("❌ package.json not found in baileys-client")
                return False
            
            # Check if node_modules exists
            node_modules = os.path.join(self.baileys_dir, "node_modules")
            if not os.path.exists(node_modules):
                logger.warning("⚠️ node_modules not found, running npm install...")
                self.install_dependencies()
            
            logger.info("✅ Baileys dependencies check passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Dependency check failed: {e}")
            return False
    
    def install_dependencies(self) -> bool:
        """Install Node.js dependencies for Baileys scraper"""
        try:
            logger.info("📦 Installing Baileys dependencies...")
            
            result = subprocess.run(['npm', 'install'], 
                                  cwd=self.baileys_dir,
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("✅ Dependencies installed successfully")
                return True
            else:
                logger.error(f"❌ npm install failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False
    
    def start_scraper(self) -> bool:
        """Start the Baileys WhatsApp scraper"""
        try:
            if not self.check_dependencies():
                return False
            
            logger.info("🚀 Starting Baileys WhatsApp scraper...")
            
            # Start the Node.js scraper process
            self.process = subprocess.Popen(
                ['node', 'index.js'],
                cwd=self.baileys_dir,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Give it a moment to start
            time.sleep(3)
            
            # Check if process is still running
            if self.process.poll() is None:
                self.is_running = True
                logger.info("✅ Baileys scraper started successfully")
                return True
            else:
                stdout, stderr = self.process.communicate()
                logger.error(f"❌ Baileys scraper failed to start: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start Baileys scraper: {e}")
            return False
    
    def stop_scraper(self) -> bool:
        """Stop the Baileys WhatsApp scraper"""
        try:
            if self.process and self.is_running:
                logger.info("🛑 Stopping Baileys WhatsApp scraper...")
                
                self.process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning("⚠️ Graceful shutdown timeout, forcing kill...")
                    self.process.kill()
                    self.process.wait()
                
                self.is_running = False
                logger.info("✅ Baileys scraper stopped")
                return True
            else:
                logger.info("ℹ️ Baileys scraper was not running")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to stop Baileys scraper: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from the Baileys scraper"""
        try:
            result = subprocess.run(
                ['node', 'cli.js', 'stats'],
                cwd=self.baileys_dir,
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                # Parse the output to extract stats
                output = result.stdout
                stats = {
                    'running': self.is_running,
                    'output': output,
                    'last_check': datetime.now().isoformat()
                }
                
                # Try to extract job count from output
                if 'Total Jobs Scraped:' in output:
                    try:
                        job_count = int(output.split('Total Jobs Scraped:')[1].split('\n')[0].strip())
                        stats['total_jobs'] = job_count
                    except:
                        stats['total_jobs'] = 0
                
                return stats
            else:
                logger.error(f"❌ Failed to get stats: {result.stderr}")
                return {'error': result.stderr, 'running': self.is_running}
                
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {'error': str(e), 'running': self.is_running}
    
    def run_test_scrape(self) -> bool:
        """Run a test scrape to verify functionality"""
        try:
            logger.info("🧪 Running Baileys scraper test...")
            
            if not self.check_dependencies():
                return False
            
            # Get current stats
            stats = self.get_stats()
            logger.info(f"📊 Current stats: {stats}")
            
            # For now, just check if we can run the CLI
            result = subprocess.run(
                ['node', 'cli.js', 'help'],
                cwd=self.baileys_dir,
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                logger.info("✅ Baileys scraper test passed")
                return True
            else:
                logger.error(f"❌ Baileys scraper test failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Baileys scraper test error: {e}")
            return False
    
    def run_comprehensive_scrape(self) -> bool:
        """Run comprehensive scraping (start the scraper)"""
        try:
            logger.info("🚀 Running Baileys comprehensive scrape...")
            
            # For comprehensive scraping, we start the scraper
            # It will run continuously until stopped
            success = self.start_scraper()
            
            if success:
                logger.info("✅ Baileys comprehensive scrape started")
                logger.info("📱 The scraper will run continuously and collect WhatsApp job messages")
                logger.info("🔄 Use stop_scraper() to stop the process")
                return True
            else:
                logger.error("❌ Failed to start comprehensive scrape")
                return False
                
        except Exception as e:
            logger.error(f"❌ Baileys comprehensive scrape error: {e}")
            return False
    
    def export_jobs_to_database(self) -> bool:
        """Export collected jobs to the database"""
        try:
            logger.info("💾 Exporting Baileys jobs to database...")
            
            result = subprocess.run(
                ['node', 'extract-jobs.js', 'export'],
                cwd=self.baileys_dir,
                env=self.env,
                capture_output=True, text=True, timeout=120
            )
            
            if result.returncode == 0:
                logger.info("✅ Jobs exported to database successfully")
                logger.info(f"📊 Export output: {result.stdout}")
                return True
            else:
                logger.error(f"❌ Job export failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Job export error: {e}")
            return False
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'is_running') and self.is_running:
            self.stop_scraper()


if __name__ == "__main__":
    # Test the scraper
    scraper = BaileysWhatsAppScraper()
    
    print("🧪 Testing Baileys WhatsApp Scraper")
    print("=" * 40)
    
    # Test dependencies
    if scraper.check_dependencies():
        print("✅ Dependencies check passed")
    else:
        print("❌ Dependencies check failed")
        sys.exit(1)
    
    # Test stats
    stats = scraper.get_stats()
    print(f"📊 Stats: {stats}")
    
    # Test scrape
    if scraper.run_test_scrape():
        print("✅ Test scrape passed")
    else:
        print("❌ Test scrape failed")
    
    print("🎉 Baileys scraper test completed!")
