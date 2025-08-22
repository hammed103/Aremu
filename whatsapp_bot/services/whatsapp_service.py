#!/usr/bin/env python3
"""
WhatsApp Service - Handles WhatsApp API interactions
Separated from main app for better organization
"""

import logging
import requests
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.apply_button_designer import apply_button_designer

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

    def send_list_menu(
        self, phone_number: str, header: str, body: str, sections: list
    ) -> bool:
        """Send WhatsApp list message"""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "interactive",
                "interactive": {
                    "type": "list",
                    "header": {"type": "text", "text": header},
                    "body": {"text": body},
                    "action": {"button": "Choose Option", "sections": sections},
                },
            }
            return self._send_message(payload)
        except Exception as e:
            logger.error(f"Error sending list menu: {e}")
            return False

    def send_button_menu(self, phone_number: str, body: str, buttons: list) -> bool:
        """Send WhatsApp button message"""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": body},
                    "action": {"buttons": buttons},
                },
            }
            return self._send_message(payload)
        except Exception as e:
            logger.error(f"Error sending button menu: {e}")
            return False

    def send_reminder_with_stay_active_button(
        self, phone_number: str, message: str
    ) -> bool:
        """Send reminder message with Stay Active button"""
        try:
            buttons = [
                {
                    "type": "reply",
                    "reply": {"id": "stay_active_24h", "title": "⚡ Stay Active"},
                }
            ]

            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": message},
                    "action": {"buttons": buttons},
                },
            }
            return self._send_message(payload)
        except Exception as e:
            logger.error(f"Error sending reminder with button: {e}")
            # Fallback to regular message
            return self.send_message(phone_number, message)

    def send_job_with_apply_button(
        self,
        phone_number: str,
        job_summary: str,
        job_url: str = None,
        company: str = None,
        job_title: str = None,
    ) -> bool:
        """Send job message with AI summary and CTA URL button that opens website directly"""
        try:
            # If no job URL, send as regular text message
            if not job_url:
                return self.send_message(phone_number, job_summary)

            # Get smart apply button text based on context
            button_text = apply_button_designer.get_apply_button_text(
                job_url, company, job_title
            )

            # Send as CTA URL message with smart Apply button
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "interactive",
                "interactive": {
                    "type": "cta_url",
                    "body": {"text": job_summary},
                    "action": {
                        "name": "cta_url",
                        "parameters": {
                            "display_text": button_text,
                            "url": job_url,
                        },
                    },
                },
            }
            return self._send_message(payload)

        except Exception as e:
            logger.error(f"Error sending job with CTA URL button: {e}")
            # Fallback to regular message with smart formatted URL
            if job_url:
                fallback_message = (
                    f"{job_summary}\n\n"
                    f"{apply_button_designer.get_fallback_apply_section(job_url, company, job_title)}"
                )
            else:
                fallback_message = job_summary
            return self.send_message(phone_number, fallback_message)

    def _send_message(self, payload: dict) -> bool:
        """Helper method to send a message with the given payload"""
        try:
            headers = {
                "Authorization": f"Bearer {self.whatsapp_token}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                self.whatsapp_api_url, headers=headers, json=payload, timeout=10
            )

            if response.status_code == 200:
                logger.info(f"✅ Message sent to {payload['to']}")
                return True
            else:
                logger.error(
                    f"❌ Failed to send message: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"❌ Error sending WhatsApp message: {e}")
            return False
