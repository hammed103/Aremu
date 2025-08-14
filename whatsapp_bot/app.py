#!/usr/bin/env python3
"""
Aremu WhatsApp AI Bot
Intelligent job search conversations via WhatsApp
"""

import os
import json
import logging
from flask import Flask, request, jsonify
from openai import OpenAI
import requests
from datetime import datetime
import hashlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("whatsapp_bot.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)


class WhatsAppBot:
    def __init__(self):
        # Load environment variables
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.whatsapp_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.whatsapp_phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "aremu_verify_token")

        # Initialize OpenAI client
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            logger.info("✅ OpenAI client initialized")
        else:
            logger.error("❌ OpenAI API key not found")

        # WhatsApp API base URL
        self.whatsapp_api_url = (
            f"https://graph.facebook.com/v18.0/{self.whatsapp_phone_id}/messages"
        )

        # Store conversation history (in production, use a database)
        self.conversations = {}

        logger.info("🤖 Aremu WhatsApp Bot initialized")

    def verify_webhook(self, mode, token, challenge):
        """Verify WhatsApp webhook"""
        if mode == "subscribe" and token == self.verify_token:
            logger.info("✅ Webhook verified successfully")
            return challenge
        else:
            logger.error("❌ Webhook verification failed")
            return None

    def get_ai_response(self, user_message, phone_number):
        """Get AI response for user message"""
        try:
            # Get conversation history
            conversation = self.conversations.get(phone_number, [])

            # Add user message to conversation
            conversation.append({"role": "user", "content": user_message})

            # Prepare system prompt for Nigerian job search context
            system_prompt = """You are Aremu, an AI assistant specialized in helping Nigerians find jobs. You are friendly, professional, and knowledgeable about the Nigerian job market.

Key capabilities:
- Help users search for jobs in Nigeria
- Provide career advice and tips
- Assist with CV/resume guidance
- Share information about Nigerian companies and industries
- Offer interview preparation tips

Guidelines:
- Be conversational and helpful
- Use Nigerian context and understanding
- Keep responses concise for WhatsApp (under 1600 characters)
- Ask follow-up questions to better understand user needs
- Be encouraging and supportive

Current conversation context: This is a WhatsApp conversation, so keep responses mobile-friendly."""

            # Prepare messages for OpenAI
            messages = [{"role": "system", "content": system_prompt}]

            # Add recent conversation history (last 10 messages to stay within limits)
            messages.extend(conversation[-10:])

            # Get AI response
            response = self.openai_client.chat.completions.create(
                model="gpt-4", messages=messages, max_tokens=300, temperature=0.7
            )

            ai_response = response.choices[0].message.content.strip()

            # Add AI response to conversation
            conversation.append({"role": "assistant", "content": ai_response})

            # Store updated conversation
            self.conversations[phone_number] = conversation

            logger.info(f"✅ AI response generated for {phone_number}")
            return ai_response

        except Exception as e:
            logger.error(f"❌ Error generating AI response: {e}")
            return "Sorry, I'm having trouble processing your message right now. Please try again in a moment."

    def send_whatsapp_message(self, phone_number, message):
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
                self.whatsapp_api_url, headers=headers, json=payload
            )

            if response.status_code == 200:
                logger.info(f"✅ Message sent to {phone_number}")
                return True
            else:
                logger.error(f"❌ Failed to send message: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Error sending WhatsApp message: {e}")
            return False

    def process_webhook_message(self, webhook_data):
        """Process incoming WhatsApp message"""
        try:
            # Extract message data
            entry = webhook_data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})

            # Check if it's a message
            if "messages" not in value:
                return

            message = value["messages"][0]
            phone_number = message["from"]

            # Handle different message types
            if message["type"] == "text":
                user_message = message["text"]["body"]
                logger.info(f"📱 Received message from {phone_number}: {user_message}")

                # Get AI response
                ai_response = self.get_ai_response(user_message, phone_number)

                # Send response back
                self.send_whatsapp_message(phone_number, ai_response)

            else:
                # Handle other message types (images, documents, etc.)
                self.send_whatsapp_message(
                    phone_number,
                    "Hi! I can help you with job search questions. Please send me a text message and I'll be happy to assist you! 😊",
                )

        except Exception as e:
            logger.error(f"❌ Error processing webhook message: {e}")


# Initialize bot
bot = WhatsAppBot()


@app.route("/", methods=["GET"])
def home():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "active",
            "service": "Aremu WhatsApp AI Bot",
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """Verify WhatsApp webhook"""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    verification_result = bot.verify_webhook(mode, token, challenge)

    if verification_result:
        return verification_result
    else:
        return "Verification failed", 403


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    """Handle incoming WhatsApp messages"""
    try:
        webhook_data = request.get_json()
        logger.info(f"📥 Webhook received: {json.dumps(webhook_data, indent=2)}")

        # Process the message
        bot.process_webhook_message(webhook_data)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/send", methods=["POST"])
def send_message():
    """Manual endpoint to send messages (for testing)"""
    try:
        data = request.get_json()
        phone_number = data.get("phone_number")
        message = data.get("message")

        if not phone_number or not message:
            return jsonify({"error": "phone_number and message required"}), 400

        success = bot.send_whatsapp_message(phone_number, message)

        if success:
            return jsonify({"status": "sent"})
        else:
            return jsonify({"error": "Failed to send message"}), 500

    except Exception as e:
        logger.error(f"❌ Send message error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
