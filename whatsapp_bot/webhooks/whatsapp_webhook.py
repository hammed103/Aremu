#!/usr/bin/env python3
"""
WhatsApp Webhook - Handles WhatsApp webhook endpoints
Separated from main app for better organization
"""

import logging
from flask import Flask, request, jsonify
from core.bot_controller import BotController
from services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)


class WhatsAppWebhook:
    """Handles WhatsApp webhook endpoints"""

    def __init__(
        self,
        bot_controller: BotController,
        whatsapp_service: WhatsAppService,
        verify_token: str,
    ):
        """Initialize webhook handler"""
        self.bot_controller = bot_controller
        self.whatsapp_service = whatsapp_service
        self.verify_token = verify_token
        logger.info("✅ WhatsApp Webhook initialized")

    def handle_webhook_get(self, request_args: dict) -> tuple:
        """Handle GET request for webhook verification"""
        try:
            mode = request_args.get("hub.mode")
            token = request_args.get("hub.verify_token")
            challenge = request_args.get("hub.challenge")

            if mode and token:
                verification_result = self.whatsapp_service.verify_webhook(
                    mode, token, challenge, self.verify_token
                )

                if verification_result:
                    return verification_result, 200
                else:
                    return "Forbidden", 403
            else:
                return "Bad Request", 400

        except Exception as e:
            logger.error(f"❌ Error in webhook GET: {e}")
            return "Internal Server Error", 500

    def handle_webhook_post(self, webhook_data: dict) -> tuple:
        """Handle POST request for incoming messages"""
        try:
            # Parse the webhook message
            message_data = self.whatsapp_service.parse_webhook_message(webhook_data)

            if not message_data:
                return jsonify({"status": "no_message"}), 200

            phone_number, user_message = message_data

            # Process the message through bot controller
            ai_response = self.bot_controller.handle_message(phone_number, user_message)

            # Send response back to user
            success = self.whatsapp_service.send_message(phone_number, ai_response)

            if success:
                # Save conversation to database
                user_id = self.bot_controller.db.get_or_create_user(phone_number)
                # Save user message
                self.bot_controller.db.save_conversation_message(
                    user_id, "user", user_message
                )
                # Save AI response
                self.bot_controller.db.save_conversation_message(
                    user_id, "assistant", ai_response
                )

                return jsonify({"status": "success"}), 200
            else:
                return jsonify({"status": "send_failed"}), 500

        except Exception as e:
            logger.error(f"❌ Error in webhook POST: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
