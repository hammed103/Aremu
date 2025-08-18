#!/usr/bin/env python3
"""
Aremu WhatsApp AI Bot - Main Application
Clean, organized architecture with separation of concerns
"""

import os
from flask import Flask, request, jsonify, send_from_directory, send_file
from dotenv import load_dotenv
from core.bot_controller import BotController
from services.whatsapp_service import WhatsAppService
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

# Initialize bot controller and services
bot_controller = BotController(openai_api_key, whatsapp_token, whatsapp_phone_id)
whatsapp_service = WhatsAppService(whatsapp_token, whatsapp_phone_id)
webhook_handler = WhatsAppWebhook(bot_controller, whatsapp_service, verify_token)

logger.info("🤖 Aremu WhatsApp Bot initialized with clean architecture")


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

    app.run(host="0.0.0.0", port=port, debug=debug_mode)
