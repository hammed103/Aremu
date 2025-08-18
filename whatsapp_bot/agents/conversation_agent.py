#!/usr/bin/env python3
"""
Conversation Agent - Handles AI conversations and responses
Separated from main app for better organization
"""

import logging
from openai import OpenAI
from typing import Dict, List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cv_analyzer import CVAnalyzer
from nigerian_career_advisor import NigerianCareerAdvisor

logger = logging.getLogger(__name__)


class ConversationAgent:
    """Handles AI conversations and intelligent responses"""

    def __init__(self, openai_api_key: str):
        """Initialize the conversation agent"""
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.cv_analyzer = CVAnalyzer(self.openai_client)
        self.career_advisor = NigerianCareerAdvisor()
        logger.info(
            "✅ Conversation Agent initialized with CV analyzer and career advisor"
        )

    def generate_response(
        self,
        user_message: str,
        user_preferences: Dict,
        user_name: Optional[str] = None,
        conversation_history: List[Dict] = None,
    ) -> str:
        """Generate intelligent response based on user message and context"""
        try:
            # Prepare system prompt for natural conversation
            system_prompt = self._create_system_prompt(user_preferences, user_name)

            # Prepare conversation messages
            messages = [{"role": "system", "content": system_prompt}]

            # Add conversation history if available
            if conversation_history:
                messages.extend(conversation_history[-10:])  # Last 10 messages

            # Add current user message
            messages.append({"role": "user", "content": user_message})

            # Generate response
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=messages,
                max_tokens=5000,
                temperature=0.7,
            )

            ai_response = response.choices[0].message.content.strip()
            logger.info(
                f"🤖 Generated natural response for user: {user_name or 'Unknown'}"
            )

            return ai_response

        except Exception as e:
            logger.error(f"❌ Error generating AI response: {e}")
            return (
                "I'm having trouble responding right now. Please try again in a moment."
            )

    def _create_system_prompt(
        self, user_preferences: Dict, user_name: Optional[str]
    ) -> str:
        """Create system prompt for realistic responses like in scenarios"""
        can_show_jobs = bool(user_preferences.get("preferences_confirmed"))

        return f"""You are Aremu, a friendly Nigerian job search assistant. Keep responses SHORT and ACTION-ORIENTED.

USER PROFILE:
- Name: {user_name or "there"}
- Job Preferences: {user_preferences}

PERSONALITY: Friendly, helpful, CONCISE. Get straight to the point.

KEY PRIORITY - JOB PREFERENCE DETECTION:
When users mention looking for jobs (e.g., "I need software developer jobs", "I'm looking for sales roles"), IMMEDIATELY guide them to set preferences:

"Nice! To get you job alerts for [job type], type 'settings' to set up your preferences. I'll send you matching opportunities as soon as they're available!"

KEEP RESPONSES SHORT:
- 1-2 sentences maximum for most responses
- Be helpful but not wordy
- Focus on ACTION, not long explanations

NATURAL RESPONSES:
- Job search requests: "Type 'settings' to set up job alerts for [role]!"
- CV requests: "Send your CV and I'll review it for the Nigerian market!"
- Salary questions: "For [role] in Lagos: ₦X-₦Y monthly. Want specific tips?"
- Interview help: "I can help you prepare! What's the role and company?"
- General chat: Keep it brief and friendly

NIGERIAN CONTEXT:
- Use Naira (₦) for salaries
- Mention Lagos, Abuja when relevant
- Keep it local but CONCISE

CRITICAL RULES:
- NEVER give long lectures or explanations
- ALWAYS prioritize getting users to set job preferences
- Direct job searches to "Show Jobs" command
- Be helpful but BRIEF

Focus on ACTIONS, not words!"""

    # The AI will handle all requests naturally in conversation
    # No need for separate intent detection or helper methods


class PreferenceParsingAgent:
    """Handles parsing of user preferences from forms using LLM"""

    def __init__(self, openai_api_key: str):
        """Initialize the preference parsing agent"""
        self.openai_client = OpenAI(api_key=openai_api_key)
        logger.info("✅ Preference Parsing Agent initialized")

    def is_form_submission(self, message: str) -> bool:
        """Use heuristic pattern matching to detect form submissions"""

        # Clean the message for analysis
        message_lower = message.lower().strip()
        lines = [line.strip() for line in message.split("\n") if line.strip()]

        # Form indicators - specific patterns that suggest a form
        form_indicators = [
            # Form field patterns
            "name:",
            "full name:",
            "my name is",
            "job:",
            "role:",
            "position:",
            "looking for",
            "location:",
            "city:",
            "state:",
            "prefer",
            "salary:",
            "pay:",
            "expect",
            "experience:",
            "years:",
            "remote",
            "hybrid",
            "onsite",
            # Form-like structure indicators
            "ngn",
            "₦",
            "naira",
            "dollar",
            "lagos",
            "abuja",
            "port harcourt",
            "developer",
            "engineer",
            "manager",
            "analyst",
        ]

        # Check for form-like structure
        has_multiple_lines = len(lines) >= 2
        has_colons = message.count(":") >= 2
        has_form_keywords = (
            sum(1 for indicator in form_indicators if indicator in message_lower) >= 3
        )

        # Check for structured data patterns
        has_structured_data = any(
            [
                # Multiple field-value pairs
                has_colons and has_multiple_lines,
                # Salary mentions with numbers
                any(char.isdigit() for char in message)
                and any(
                    word in message_lower for word in ["salary", "pay", "ngn", "₦"]
                ),
                # Location + job type combination
                any(loc in message_lower for loc in ["lagos", "abuja", "port harcourt"])
                and any(
                    job in message_lower
                    for job in ["developer", "engineer", "manager", "analyst", "sales"]
                ),
                # Experience level mentions
                "year" in message_lower and any(char.isdigit() for char in message),
            ]
        )

        # Form submission criteria
        is_form = (
            (has_form_keywords and has_structured_data)
            or (
                # Strong form indicators
                has_colons
                and has_multiple_lines
                and len(message) > 50
            )
            or (
                # Explicit form submission phrases
                any(
                    phrase in message_lower
                    for phrase in [
                        "here are my details",
                        "my information",
                        "my preferences",
                        "filled form",
                        "completed form",
                        "here is my",
                    ]
                )
            )
        )

        if is_form:
            logger.info(
                f"📝 Form submission detected: {len(lines)} lines, {message.count(':')} colons, {len(message)} chars"
            )

        return is_form

    def parse_preferences_from_form(self, form_message: str) -> Dict:
        """Parse user preferences from filled form using heuristic detection + AI parsing"""

        # First use heuristic to check if this is a form submission
        if not self.is_form_submission(form_message):
            logger.info(f"📝 Not a form submission - skipping preference parsing")
            return {}

        try:
            parse_prompt = f"""Extract job preferences from this user message: "{form_message}"

Return ONLY a JSON object with these exact fields (only include fields with actual data):

{{
  "full_name": "user's full name",
  "job_roles": ["job title 1", "job title 2"],
  "preferred_locations": ["location 1", "location 2"],
  "salary_min": number_only,
  "salary_currency": "NGN",
  "years_of_experience": number_only,
  "work_arrangements": ["Remote", "Hybrid", "Onsite"]
}}

STRICT RULES:
- Extract ONLY information explicitly mentioned by the user
- Do NOT infer or assume information not stated
- Use arrays for multiple values
- Numbers should be integers, not strings
- If salary has ₦ symbol, set currency to "NGN"
- If no currency mentioned, default to "NGN"
- Omit fields if no relevant information provided
- Return valid JSON only, no other text

JSON:"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": parse_prompt}],
                max_tokens=300,
                temperature=0.1,
            )

            result = response.choices[0].message.content.strip()

            # Parse JSON response
            import json

            if "{" in result and "}" in result:
                start = result.find("{")
                end = result.rfind("}") + 1
                json_str = result[start:end]
                preferences = json.loads(json_str)
                logger.info(f"🤖 LLM parsed preferences: {preferences}")
                return preferences
            else:
                logger.error(f"❌ No JSON in LLM response: {result}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error parsing preferences with LLM: {e}")
            return {}
