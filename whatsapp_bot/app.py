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
    reminder_service.create_reminder_log_table()

    logger.info("🤖 Aremu WhatsApp Bot initialized with clean architecture")
    BOT_INITIALIZED = True
except Exception as e:
    logger.error(f"❌ Failed to initialize bot components: {e}")
    logger.info("🌐 Starting in frontend-only mode")
    bot_controller = None
    whatsapp_service = None
    webhook_handler = None
    reminder_service = None
    BOT_INITIALIZED = False


def run_reminder_daemon():
    """Run reminder daemon in background thread"""
    if reminder_service and BOT_INITIALIZED:
        import time

        logger.info("🕐 Starting reminder daemon in background")

        while True:
            try:
                reminder_service.run_reminder_cycle()
                time.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"❌ Reminder daemon error: {e}")
                time.sleep(60)  # Wait 1 minute on error


# Flask Routes
@app.route("/webhook", methods=["GET"])
def webhook_get():
    """Handle webhook verification"""
    return webhook_handler.handle_webhook_get(request.args)


@app.route("/webhook", methods=["POST"])
def webhook_post():
    """Handle incoming WhatsApp messages"""
    return webhook_handler.handle_webhook_post(request.get_json())


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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug_mode = os.environ.get("FLASK_ENV") != "production"

    logger.info(f"🚀 Starting Aremu unified server on port {port}")
    logger.info(f"📱 Frontend available at: http://localhost:{port}/")
    logger.info(f"🤖 WhatsApp webhook at: http://localhost:{port}/webhook")

    # Start reminder daemon in background thread (only in production)
    if not debug_mode and BOT_INITIALIZED:
        reminder_thread = threading.Thread(target=run_reminder_daemon, daemon=True)
        reminder_thread.start()
        logger.info("🕐 Reminder daemon started in background")

    app.run(host="0.0.0.0", port=port, debug=debug_mode)
