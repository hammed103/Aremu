#!/usr/bin/env python3
"""
WhatsApp Service - Handles WhatsApp API interactions
Separated from main app for better organization
"""

import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Handles WhatsApp API interactions"""

    def __init__(self, whatsapp_token: str, whatsapp_phone_id: str):
        """Initialize WhatsApp service"""
        self.whatsapp_token = whatsapp_token
        self.whatsapp_phone_id = whatsapp_phone_id
        self.whatsapp_api_url = (
            f"https://graph.facebook.com/v18.0/{whatsapp_phone_id}/messages"
        )
        logger.info("✅ WhatsApp Service initialized")

    def send_message(self, phone_number: str, message: str) -> bool:
        """Send message via WhatsApp API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.whatsapp_token}",
                "Content-Type": "application/json",
            }

            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "text",
                "text": {"body": message},
            }

            response = requests.post(
                self.whatsapp_api_url, headers=headers, json=payload, timeout=10
            )

            if response.status_code == 200:
                logger.info(f"✅ Message sent to {phone_number}")
                return True
            else:
                logger.error(
                    f"❌ Failed to send message: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"❌ Error sending WhatsApp message: {e}")
            return False

    def verify_webhook(
        self, mode: str, token: str, challenge: str, verify_token: str
    ) -> Optional[str]:
        """Verify WhatsApp webhook"""
        if mode == "subscribe" and token == verify_token:
            logger.info("✅ Webhook verified successfully")
            return challenge
        else:
            logger.error("❌ Webhook verification failed")
            return None

    def parse_webhook_message(self, webhook_data: dict) -> Optional[tuple]:
        """Parse incoming webhook message and extract phone number and message"""
        try:
            if "entry" not in webhook_data:
                return None

            for entry in webhook_data["entry"]:
                if "changes" not in entry:
                    continue

                for change in entry["changes"]:
                    if change.get("field") != "messages":
                        continue

                    value = change.get("value", {})
                    messages = value.get("messages", [])

                    for message in messages:
                        if message.get("type") == "text":
                            phone_number = message.get("from")
                            message_text = message.get("text", {}).get("body", "")

                            if phone_number and message_text:
                                logger.info(
                                    f"📱 Received message from {phone_number}: {message_text[:50]}..."
                                )
                                return phone_number, message_text

            return None

        except Exception as e:
            logger.error(f"❌ Error parsing webhook message: {e}")
            return None
