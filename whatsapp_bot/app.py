#!/usr/bin/env python3
"""
Aremu WhatsApp AI Bot - Main Application
Clean, organized architecture with separation of concerns
"""

import os
import threading
from flask import Flask, request, jsonify, send_from_directory, send_file
from dotenv import load_dotenv
from core.bot_controller import BotController
from services.whatsapp_service import WhatsAppService
from services.reminder_service import ReminderService
from services.scraper_service import ScraperService
from services.automated_cleanup_service import AutomatedCleanupService
from webhooks.whatsapp_webhook import WhatsAppWebhook
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Set up logging
logger = setup_logger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure static file serving for frontend
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
app.static_folder = FRONTEND_DIR


def run_reminder_daemon():
    """Run reminder daemon in background thread"""
    # Import here to avoid circular imports
    import time

    logger.info("🕐 Starting reminder daemon in background")
    cycle_count = 0

    while True:
        try:
            cycle_count += 1
            logger.info(f"🔄 Reminder daemon cycle #{cycle_count} starting")

            sent_count = reminder_service.run_reminder_cycle()

            if sent_count > 0:
                logger.info(f"✅ Cycle #{cycle_count}: {sent_count} reminders sent")
            else:
                logger.info(f"✅ Cycle #{cycle_count}: No reminders needed")

            logger.info("😴 Sleeping for 300 seconds until next cycle...")
            time.sleep(300)  # Check every 5 minutes

        except Exception as e:
            logger.error(f"❌ Reminder daemon cycle #{cycle_count} error: {e}")
            logger.info("⏳ Waiting 60 seconds before retry...")
            time.sleep(60)  # Wait 1 minute on error


# Initialize global components
openai_api_key = os.getenv("OPENAI_API_KEY")
whatsapp_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
whatsapp_phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "aremu_verify_token")

# Initialize bot controller and services (with error handling)
try:
    bot_controller = BotController(openai_api_key, whatsapp_token, whatsapp_phone_id)
    whatsapp_service = WhatsAppService(whatsapp_token, whatsapp_phone_id)
    webhook_handler = WhatsAppWebhook(bot_controller, whatsapp_service, verify_token)

    # Initialize reminder service
    reminder_service = ReminderService(whatsapp_service)

    # Initialize scraper service
    scraper_service = ScraperService()

    # Initialize cleanup service
    cleanup_service = AutomatedCleanupService()

    # Check table status and create if needed
    if not reminder_service.check_table_status():
        reminder_service.create_reminder_log_table()
    else:
        logger.info("📋 Reminder log table already exists")

    logger.info("🤖 Aremu WhatsApp Bot initialized with clean architecture")
    BOT_INITIALIZED = True
    logger.info("Bot initialized set to True")

    # Start background services in production
    is_production = os.environ.get("FLASK_ENV") == "production"
    if is_production and BOT_INITIALIZED:
        # Start reminder daemon
        reminder_thread = threading.Thread(target=run_reminder_daemon, daemon=True)
        reminder_thread.start()
        logger.info("🕐 Reminder daemon started in background thread")

        # Start scraper daemon
        scraper_service.start_daemon()
        logger.info("🔧 Scraper daemon started in background thread")

        # Start cleanup service
        cleanup_service.start_automated_cleanup(interval_hours=5)
        logger.info("🧹 Cleanup service started (every 5 hours)")
    else:
        logger.info(
            f"🕐 Background services not started (production: {is_production}, bot_init: {BOT_INITIALIZED})"
        )
except Exception as e:
    logger.error(f"❌ Failed to initialize bot components: {e}")
    logger.info("🌐 Starting in frontend-only mode")
    bot_controller = None
    whatsapp_service = None
    webhook_handler = None
    reminder_service = None
    scraper_service = None
    cleanup_service = None
    BOT_INITIALIZED = False


# Helper functions
def _is_system_message(response: str) -> bool:
    """Check if response is a system message that shouldn't be sent to user"""
    system_messages = [
        "Menu sent!",
        "Welcome setup sent!",
        "Setup completion with buttons sent!",
        "Preferences confirmed with options sent!",
        "Resume setup sent!",
        "Preference update menu sent!",
    ]
    return any(msg in response for msg in system_messages)


# Flask Routes
@app.route("/webhook", methods=["GET"])
def webhook_get():
    """Handle webhook verification"""
    return webhook_handler.handle_webhook_get(request.args)


@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle WhatsApp webhook including interactive messages"""
    try:
        data = request.get_json()

        if data.get("object") == "whatsapp_business_account":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        for message in change.get("value", {}).get("messages", []):
                            phone_number = message.get("from")

                            # Handle interactive messages (menu selections)
                            if message.get("type") == "interactive":
                                interactive_data = message.get("interactive", {})
                                response = bot_controller.handle_interactive_message(
                                    phone_number, interactive_data
                                )

                                # Send response only if it's not a system message
                                if response and not _is_system_message(response):
                                    bot_controller.whatsapp_service.send_message(
                                        phone_number, response
                                    )

                            # Handle text messages
                            elif message.get("type") == "text":
                                user_message = message.get("text", {}).get("body", "")
                                response = bot_controller.handle_message(
                                    phone_number, user_message
                                )

                                # Send response only if it's not a system message
                                if response and not _is_system_message(response):
                                    bot_controller.whatsapp_service.send_message(
                                        phone_number, response
                                    )

                            # Handle document messages (for CV analyzer)
                            elif message.get("type") == "document":
                                # Handle CV uploads
                                response = (
                                    "📋 CV received! Analyzing... (Feature coming soon)"
                                )
                                bot_controller.whatsapp_service.send_message(
                                    phone_number, response
                                )

        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"status": "error"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "service": "Aremu WhatsApp Bot + Frontend",
            "architecture": "Clean & Organized",
        }
    )


# Frontend Routes
@app.route("/")
def serve_frontend():
    """Serve the main frontend page"""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def serve_static_files(filename):
    """Serve static files (CSS, JS, images, etc.)"""
    try:
        return send_from_directory(FRONTEND_DIR, filename)
    except FileNotFoundError:
        # If file not found, serve index.html for SPA routing
        return send_from_directory(FRONTEND_DIR, "index.html")


# API Routes (for potential frontend-backend communication)
@app.route("/api/status", methods=["GET"])
def api_status():
    """API status endpoint for frontend"""
    return jsonify(
        {
            "status": "online",
            "service": "Aremu AI Job Bot",
            "whatsapp_bot": "active",
        }
    )


@app.route("/api/scrapers/status", methods=["GET"])
def api_scrapers_status():
    """Get status of all scrapers"""
    if scraper_service is None:
        return jsonify({"error": "Scraper service not initialized"}), 500

    return jsonify(scraper_service.get_status())


@app.route("/api/scrapers/run", methods=["POST"])
def api_run_scraper():
    """Manually trigger a scraper run"""
    if scraper_service is None:
        return jsonify({"error": "Scraper service not initialized"}), 500

    data = request.get_json() or {}
    scraper_name = data.get("scraper", "all")

    result = scraper_service.run_manual_scrape(scraper_name)

    if result["status"] == "success":
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@app.route("/api/scrapers/start", methods=["POST"])
def api_start_scraper_daemon():
    """Start the scraper daemon"""
    if scraper_service is None:
        return jsonify({"error": "Scraper service not initialized"}), 500

    scraper_service.start_daemon()
    return jsonify({"status": "success", "message": "Scraper daemon started"})


@app.route("/api/scrapers/stop", methods=["POST"])
def api_stop_scraper_daemon():
    """Stop the scraper daemon"""
    if scraper_service is None:
        return jsonify({"error": "Scraper service not initialized"}), 500

    scraper_service.stop_daemon()
    return jsonify({"status": "success", "message": "Scraper daemon stopped"})


@app.route("/api/cleanup/run", methods=["POST"])
def api_run_cleanup():
    """Run manual cleanup operation"""
    if cleanup_service is None:
        return jsonify({"error": "Cleanup service not initialized"}), 500

    try:
        success = cleanup_service.run_full_cleanup()
        if success:
            return jsonify({"status": "success", "message": "Cleanup completed"})
        else:
            return jsonify({"status": "error", "message": "Cleanup failed"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/cleanup/stats", methods=["GET"])
def api_cleanup_stats():
    """Get cleanup statistics"""
    if cleanup_service is None:
        return jsonify({"error": "Cleanup service not initialized"}), 500

    try:
        cursor = cleanup_service.connection.cursor()

        # Count total jobs
        cursor.execute("SELECT COUNT(*) FROM canonical_jobs")
        total_jobs = cursor.fetchone()[0]

        # Count old jobs (5 days)
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM canonical_jobs
            WHERE scraped_at < NOW() - INTERVAL '5 days'
            OR scraped_at IS NULL
            """
        )
        old_jobs = cursor.fetchone()[0]

        # Count potential duplicates
        cursor.execute(
            """
            WITH duplicates AS (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY
                            LOWER(TRIM(title)),
                            LOWER(TRIM(company)),
                            LOWER(TRIM(COALESCE(location, '')))
                        ORDER BY scraped_at DESC, id DESC
                    ) as row_num
                FROM canonical_jobs
                WHERE title IS NOT NULL
                AND company IS NOT NULL
            )
            SELECT COUNT(*)
            FROM duplicates
            WHERE row_num > 1
            """
        )
        duplicate_jobs = cursor.fetchone()[0]

        return jsonify(
            {
                "status": "success",
                "stats": {
                    "total_jobs": total_jobs,
                    "old_jobs": old_jobs,
                    "duplicate_jobs": duplicate_jobs,
                    "jobs_after_cleanup": total_jobs - old_jobs - duplicate_jobs,
                },
            }
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug_mode = os.environ.get("FLASK_ENV") != "production"

    logger.info(f"🚀 Starting Aremu unified server on port {port}")
    logger.info(f"📱 Frontend available at: http://localhost:{port}/")
    logger.info(f"🤖 WhatsApp webhook at: http://localhost:{port}/webhook")
    logger.info(
        "🕐 Background services (reminders + scrapers) start in production mode"
    )

    app.run(host="0.0.0.0", port=port, debug=debug_mode)
