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
from database_manager import DatabaseManager
import uuid

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

        # Initialize database manager
        self.db = DatabaseManager()
        self.db.ensure_tables_exist()

        # Session tracking
        self.current_sessions = {}  # Track active session IDs

        logger.info("🤖 Aremu WhatsApp Bot initialized")

    def manage_conversation_memory(self):
        """Clean up old conversations to prevent memory issues"""
        if len(self.conversations) > self.max_users:
            # Remove oldest conversations (simple FIFO)
            oldest_users = list(self.conversations.keys())[: -self.max_users]
            for user in oldest_users:
                del self.conversations[user]
                if user in self.user_sessions:
                    del self.user_sessions[user]
            logger.info(f"🧹 Cleaned up {len(oldest_users)} old conversations")

    def get_user_conversation(self, phone_number):
        """Get conversation history for a user"""
        conversation = self.conversations.get(phone_number, [])

        # Trim conversation if too long
        if len(conversation) > self.max_conversation_length:
            # Keep system context + recent messages
            conversation = conversation[-self.max_conversation_length :]
            self.conversations[phone_number] = conversation

        return conversation

    def update_user_session(self, phone_number, user_message, ai_response):
        """Update user session and conversation history"""
        from datetime import datetime

        # Update session info
        self.user_sessions[phone_number] = {
            "last_message": datetime.now().isoformat(),
            "message_count": self.user_sessions.get(phone_number, {}).get(
                "message_count", 0
            )
            + 1,
        }

        # Get current conversation
        conversation = self.get_user_conversation(phone_number)

        # Add new messages
        conversation.append({"role": "user", "content": user_message})
        conversation.append({"role": "assistant", "content": ai_response})

        # Store updated conversation
        self.conversations[phone_number] = conversation

        # Clean up memory if needed
        self.manage_conversation_memory()

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
            # Get or create user in database
            user_id = self.db.get_or_create_user(phone_number)
            if not user_id:
                return "Sorry, I'm having trouble right now. Please try again."

            # Get conversation history from database
            conversation = self.db.get_conversation_history(user_id, limit=10)

            # Add current user message to conversation
            conversation.append({"role": "user", "content": user_message})

            # Get user info for personalization
            user_preferences = self.db.get_user_preferences(user_id)
            cursor = self.db.connection.cursor()
            cursor.execute("SELECT name FROM users WHERE id = %s", (user_id,))
            user_name = cursor.fetchone()
            user_name = user_name[0] if user_name and user_name[0] else None

            # Analyze user preferences completeness
            missing_prefs = self.analyze_missing_preferences(user_preferences)

            # Prepare intelligent system prompt
            system_prompt = f"""You are Aremu, a friendly AI job search assistant in TEST MODE. You help Nigerians find their perfect jobs through natural conversation.

USER PROFILE:
- Name: {user_name or "Unknown"}
- Current preferences: {user_preferences}
- Missing info: {missing_prefs}

PERSONALITY: Be warm, conversational, and genuinely interested in helping. Adapt your tone based on the user's energy. Use their name when you know it.

INTELLIGENCE GUIDELINES:
1. **You are the ONLY preference detector**: No other system will extract preferences - YOU must detect everything
2. **Assess what you know**: Based on their saved preferences, intelligently decide what to ask next
3. **Ask smart questions**: If they have no job type, ask about their interests/skills. If no location preference, ask about remote vs office work
4. **Be contextual**: If they mention a job, naturally ask follow-up questions about their preferences for that type of role
5. **Don't overwhelm**: Ask 1-2 relevant questions at a time, not everything at once
6. **Show jobs when ready**: Once you have enough info (job type + at least 1 other preference), offer to show sample jobs

CRITICAL: You MUST always end your response with a PREFERENCES_DETECTED section if you detect ANY preferences or name:

PREFERENCES_DETECTED: {{
  "job_type": "software developer",
  "employment_type": "full-time",
  "salary_currency": "USD",
  "location_preference": "remote",
  "experience_level": "mid",
  "name": "John"
}}

Only include fields you actually detect. This is MANDATORY for the system to work.

SAMPLE JOB FORMAT (when showing jobs):
"1️⃣ [Job Title] - [Company], [Location], [Salary], Requirements: [brief], Apply: [email]"

IMPORTANT:
- Always end with "I'm still in test mode, so these are sample jobs! 🤖" when showing jobs
- Keep responses under 1600 characters
- Be natural and conversational, not robotic
- Ask questions that feel genuine, not like a form"""

            # Prepare messages for OpenAI
            messages = [{"role": "system", "content": system_prompt}]

            # Add recent conversation history (last 10 messages to stay within limits)
            messages.extend(conversation[-10:])

            # Get AI response
            response = self.openai_client.chat.completions.create(
                model="gpt-4", messages=messages, max_tokens=300, temperature=0.7
            )

            ai_response = response.choices[0].message.content.strip()

            # Extract AI-detected preferences from response
            clean_response, ai_detected_prefs = self.extract_ai_preferences(ai_response)

            # Generate session ID for this conversation
            session_id = self.current_sessions.get(phone_number, str(uuid.uuid4()))
            self.current_sessions[phone_number] = session_id

            # Save conversation to database (use clean response without preference data)
            self.db.save_conversation_message(user_id, "user", user_message, session_id)
            self.db.save_conversation_message(
                user_id, "assistant", clean_response, session_id
            )

            # Save AI-detected preferences (AI handles ALL detection now)
            if ai_detected_prefs:
                self.save_ai_detected_preferences(user_id, ai_detected_prefs)
                logger.info(f"🤖 AI detected and saved: {ai_detected_prefs}")
            else:
                logger.info("🤖 AI didn't detect any new preferences in this message")

            logger.info(f"✅ AI response generated and saved for {phone_number}")
            return clean_response  # Return clean response without preference data

        except Exception as e:
            logger.error(f"❌ Error generating AI response: {e}")
            return "Sorry, I'm having trouble processing your message right now. Please try again in a moment."

    def extract_ai_preferences(self, ai_response):
        """Extract preferences detected by AI from response"""
        import re
        import json

        # Look for PREFERENCES_DETECTED section
        pattern = r"PREFERENCES_DETECTED:\s*(\{[^}]+\})"
        match = re.search(pattern, ai_response, re.DOTALL)

        if match:
            try:
                # Extract the JSON-like content
                prefs_text = match.group(1)
                # Clean up the format (remove comments in parentheses)
                prefs_text = re.sub(r"\s*\([^)]+\)", "", prefs_text)
                # Parse as JSON
                preferences = json.loads(prefs_text)

                # Remove the preferences section from response
                clean_response = re.sub(
                    r"PREFERENCES_DETECTED:.*", "", ai_response, flags=re.DOTALL
                ).strip()

                logger.info(f"🤖 AI detected preferences: {preferences}")
                return clean_response, preferences

            except Exception as e:
                logger.error(f"❌ Error parsing AI preferences: {e}")

        # No preferences detected
        return ai_response, None

    def save_ai_detected_preferences(self, user_id, preferences):
        """Save preferences detected by AI"""
        try:
            # Filter out None values and clean up
            clean_prefs = {}
            for key, value in preferences.items():
                if value and value.strip():
                    clean_prefs[key] = value.strip()

            if clean_prefs:
                # Handle name separately
                if "name" in clean_prefs:
                    self.db.update_user_name(user_id, clean_prefs["name"])
                    del clean_prefs["name"]

                # Save job preferences
                if clean_prefs:
                    self.db.save_user_preferences(user_id, clean_prefs)
                    logger.info(f"💾 Saved AI-detected preferences: {clean_prefs}")

        except Exception as e:
            logger.error(f"❌ Error saving AI preferences: {e}")

    def analyze_missing_preferences(self, user_preferences):
        """Analyze what preferences are missing to guide intelligent questioning"""
        essential_prefs = [
            "job_type",
            "employment_type",
            "salary_currency",
            "location_preference",
            "experience_level",
        ]

        missing = []
        for pref in essential_prefs:
            if not user_preferences.get(pref):
                missing.append(pref)

        # Convert to human-readable format
        missing_readable = []
        pref_map = {
            "job_type": "what type of job they want",
            "employment_type": "full-time vs part-time preference",
            "salary_currency": "currency preference (Naira/Dollar)",
            "location_preference": "location/remote preference",
            "experience_level": "experience level",
        }

        for pref in missing:
            if pref in pref_map:
                missing_readable.append(pref_map[pref])

        return missing_readable

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
