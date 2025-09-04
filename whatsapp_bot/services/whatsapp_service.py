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
        whatsapp_number: str = None,
        email: str = None,
    ) -> bool:
        """Send job message with single CTA URL button (WhatsApp Cloud API limitation)"""
        try:
            logger.info(
                f"🔘 SEND_JOB_WITH_APPLY_BUTTON: Starting for phone={phone_number}"
            )
            logger.info(f"🔗 SEND_JOB_WITH_APPLY_BUTTON: job_url={job_url}")
            logger.info(
                f"📱 SEND_JOB_WITH_APPLY_BUTTON: whatsapp_number={whatsapp_number}"
            )
            logger.info(f"📧 SEND_JOB_WITH_APPLY_BUTTON: email={email}")

            # WhatsApp Cloud API only supports ONE CTA URL button per message
            # Priority logic for CTA selection (as requested):
            # 1. WhatsApp contact (highest priority - direct contact)
            # 2. Email contact (secondary - traditional contact)
            # 3. Job URL (tertiary - application link)

            # For multiple contact methods, we'll include them in the message text
            # and use the highest priority one as the CTA button

            cta_url = None
            cta_button_text = None
            additional_contacts = []

            # Determine primary CTA and collect additional contact methods
            if whatsapp_number:
                cta_url = self._format_whatsapp_link(whatsapp_number)
                cta_button_text = self._get_whatsapp_button_text(company, job_title)
                logger.info(f"� Primary CTA: WhatsApp")

                # Add secondary contact methods to message text
                if email:
                    additional_contacts.append(f"� Email: {email}")
                if job_url:
                    additional_contacts.append(f"� Apply: {job_url}")

            elif email:
                cta_url = f"mailto:{email}"
                cta_button_text = self._get_email_button_text(company, job_title)
                logger.info(f"� Primary CTA: Email")

                # Add job URL as secondary contact method
                if job_url:
                    additional_contacts.append(f"� Apply: {job_url}")

            elif job_url:
                cta_url = job_url
                cta_button_text = apply_button_designer.get_apply_button_text(
                    job_url, company, job_title
                )
                logger.info(f"� Primary CTA: Job URL")

            else:
                # No contact methods available - send as regular message
                logger.info(
                    f"❌ No contact methods available - sending as regular message"
                )
                return self.send_message(phone_number, job_summary)

            # Enhance job summary with additional contact methods
            enhanced_summary = job_summary
            if additional_contacts:
                enhanced_summary += "\n\n" + "\n".join(additional_contacts)

            # Ensure button text fits WhatsApp's 20 character limit
            cta_button_text = self._ensure_button_text_length(cta_button_text)

            logger.info(f"🔘 CTA Button: '{cta_button_text}' -> {cta_url}")

            # Send as CTA URL message
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "interactive",
                "interactive": {
                    "type": "cta_url",
                    "body": {"text": enhanced_summary},
                    "action": {
                        "name": "cta_url",
                        "parameters": {
                            "display_text": cta_button_text,
                            "url": cta_url,
                        },
                    },
                },
            }
            logger.info(f"📤 Sending CTA URL payload")
            return self._send_message(payload)

        except Exception as e:
            logger.error(f"Error sending job with apply button: {e}")
            # Fallback to regular message
            return self.send_message(phone_number, job_summary)

    def send_job_with_whatsapp_button(
        self,
        phone_number: str,
        job_summary: str,
        whatsapp_number: str,
        company: str = None,
        job_title: str = None,
    ) -> bool:
        """Send job message with WhatsApp contact CTA button"""
        try:
            # Format WhatsApp number for wa.me link
            wa_link = self._format_whatsapp_link(whatsapp_number)

            # Get smart WhatsApp button text (ensure 20 char limit)
            button_text = self._ensure_button_text_length(
                self._get_whatsapp_button_text(company, job_title)
            )

            # Send as CTA URL message with WhatsApp contact button
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
                            "url": wa_link,
                        },
                    },
                },
            }
            return self._send_message(payload)

        except Exception as e:
            logger.error(f"Error sending job with WhatsApp button: {e}")
            # Fallback to regular message with WhatsApp number
            fallback_message = f"{job_summary}\n\n📱 WhatsApp: {whatsapp_number}"
            return self.send_message(phone_number, fallback_message)

    def send_job_with_email_button(
        self,
        phone_number: str,
        job_summary: str,
        email: str,
        company: str = None,
        job_title: str = None,
    ) -> bool:
        """Send job message with email contact CTA button"""
        try:
            # Format email for mailto link
            mailto_link = f"mailto:{email}"

            # Get email button text
            button_text = self._get_email_button_text(company, job_title)

            # Send as CTA URL message with email contact button
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
                            "url": mailto_link,
                        },
                    },
                },
            }
            return self._send_message(payload)

        except Exception as e:
            logger.error(f"Error sending job with email button: {e}")
            # Fallback to regular message with email
            fallback_message = f"{job_summary}\n\n📧 Email: {email}"
            return self.send_message(phone_number, fallback_message)

    def _format_whatsapp_link(self, whatsapp_number: str) -> str:
        """Format WhatsApp number into wa.me link"""
        try:
            # Clean the number
            clean_number = "".join(filter(str.isdigit, whatsapp_number))

            # Add country code if not present (assume Nigeria +234)
            if clean_number.startswith("0"):
                clean_number = "234" + clean_number[1:]
            elif not clean_number.startswith("234"):
                clean_number = "234" + clean_number

            return f"https://wa.me/{clean_number}"

        except Exception as e:
            logger.error(f"Error formatting WhatsApp link: {e}")
            return f"https://wa.me/{whatsapp_number}"

    def _get_whatsapp_button_text(
        self, company: str = None, job_title: str = None
    ) -> str:
        """Get smart WhatsApp button text based on context"""
        try:
            # Company-specific WhatsApp buttons (max 20 chars)
            if company:
                company_lower = company.lower()

                # Tech companies
                if "google" in company_lower:
                    return "📱 Contact Google"
                elif "microsoft" in company_lower:
                    return "📱 Contact Microsoft"
                elif "meta" in company_lower:
                    return "📱 Contact Meta"
                elif "dangote" in company_lower:
                    return "📱 Contact Dangote"
                elif "mtn" in company_lower:
                    return "📱 Contact MTN"
                elif "gtbank" in company_lower or "gtb" in company_lower:
                    return "📱 Contact GTBank"
                elif "access" in company_lower and "bank" in company_lower:
                    return "📱 Contact Access"
                elif "zenith" in company_lower:
                    return "📱 Contact Zenith"

                # Generic company name (truncate if too long)
                clean_company = company.replace("Limited", "Ltd").replace(
                    "Nigeria", "NG"
                )
                if len(clean_company) <= 10:  # Leave room for "📱 Contact "
                    return f"📱 Contact {clean_company}"

            # Role-specific WhatsApp buttons
            if job_title:
                title_lower = job_title.lower()
                if "manager" in title_lower:
                    return "📱 Contact Manager"
                elif "developer" in title_lower or "engineer" in title_lower:
                    return "📱 Contact Team"
                elif "sales" in title_lower:
                    return "📱 Contact Sales"
                elif "hr" in title_lower or "human" in title_lower:
                    return "📱 Contact HR"
                elif "finance" in title_lower:
                    return "📱 Contact Finance"
                elif "marketing" in title_lower:
                    return "📱 Contact Marketing"

            # Default professional button (19 chars - within limit)
            return "📱 Contact Employer"

        except Exception as e:
            logger.error(f"Error generating WhatsApp button text: {e}")
            return "📱 WhatsApp Employer"

    def _ensure_button_text_length(self, text: str) -> str:
        """Ensure button text is within WhatsApp's 20 character limit"""
        if len(text) <= 20:
            return text
        # Truncate and add ellipsis if needed
        return text[:17] + "..."

    def _get_email_button_text(self, company: str = None, job_title: str = None) -> str:
        """Get smart email button text based on context"""
        try:
            # Company-specific email buttons with "Send CV to..." format
            if company:
                company_lower = company.lower()

                # Tech companies
                if "google" in company_lower:
                    return "📧 Send CV to Google"
                elif "microsoft" in company_lower:
                    return "📧 Send CV to Microsoft"
                elif "meta" in company_lower:
                    return "📧 Send CV to Meta"
                elif "dangote" in company_lower:
                    return "📧 Send CV to Dangote"
                elif "mtn" in company_lower:
                    return "📧 Send CV to MTN"
                elif "gtbank" in company_lower or "gtb" in company_lower:
                    return "📧 Send CV to GTBank"
                elif "access" in company_lower and "bank" in company_lower:
                    return "📧 Send CV to Access"
                elif "zenith" in company_lower:
                    return "📧 Send CV to Zenith"

                # Generic company name (truncate if too long for button)
                clean_company = company.replace("Limited", "Ltd").replace(
                    "Nigeria", "NG"
                )
                if len(clean_company) <= 8:  # Shorter limit for "Send CV to X"
                    return f"📧 Send CV to {clean_company}"

            # Role-specific email buttons
            if job_title:
                title_lower = job_title.lower()
                if "manager" in title_lower:
                    return "📧 Send CV to Manager"
                elif "developer" in title_lower or "engineer" in title_lower:
                    return "📧 Send CV to Team"
                elif "sales" in title_lower:
                    return "📧 Send CV to Sales"
                elif "hr" in title_lower or "human" in title_lower:
                    return "📧 Send CV to HR"
                elif "finance" in title_lower:
                    return "📧 Send CV to Finance"
                elif "marketing" in title_lower:
                    return "📧 Send CV to Marketing"

            # Default professional button
            return "📧 Send CV"

        except Exception as e:
            logger.error(f"Error generating email button text: {e}")
            return "📧 Email Employer"

    def _send_message(self, payload: dict) -> bool:
        """Helper method to send a message with the given payload"""
        try:
            logger.info(
                f"📤 _SEND_MESSAGE: Sending payload type: {payload.get('type', 'unknown')}"
            )
            if payload.get("type") == "interactive":
                interactive_type = payload.get("interactive", {}).get("type", "unknown")
                logger.info(f"🔄 _SEND_MESSAGE: Interactive type: {interactive_type}")

            headers = {
                "Authorization": f"Bearer {self.whatsapp_token}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                self.whatsapp_api_url, headers=headers, json=payload, timeout=10
            )

            if response.status_code == 200:
                logger.info(f"✅ _SEND_MESSAGE: Message sent to {payload['to']}")
                return True
            else:
                logger.error(
                    f"❌ _SEND_MESSAGE: Failed to send message: {response.status_code} - {response.text}"
                )
                logger.error(f"❌ _SEND_MESSAGE: Payload was: {payload}")
                return False

        except Exception as e:
            logger.error(f"❌ _SEND_MESSAGE: Error sending WhatsApp message: {e}")
            return False
