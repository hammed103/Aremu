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
            # Check if this is a job request and handle it explicitly
            if self._is_job_request(user_message):
                return self._handle_job_request(
                    user_message, user_preferences, user_name
                )

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

        return f"""You are Aremu, an ENTHUSIASTIC Nigerian job search assistant! You're EXCITED to help people find amazing jobs. Keep responses SHORT but ENERGETIC.

USER PROFILE:
- Name: {user_name or "there"}
- Job Preferences: {user_preferences}

PERSONALITY: ENTHUSIASTIC, helpful, ENERGETIC, CONCISE. Get straight to the point with excitement!

GREETING RESPONSES (hi, hello, hey, good morning, etc.):
Be ENTHUSIASTIC and show what you can do! Examples:
"🚀 Hey {user_name or 'there'}! I'm Aremu, your AI job search assistant! I can help you find amazing jobs, review your CV, and prep for interviews! What would you like to do today?"

"🎯 Hi {user_name or 'there'}! Ready to land your dream job? I can search thousands of opportunities, analyze your CV, and help you ace interviews! Type 'menu' to see what I can do!"

"💼 Hello {user_name or 'there'}! I'm here to supercharge your job search! I can find perfect job matches, review your CV, and help you prepare for interviews! What can I help you with?"

KEY PRIORITY - INTELLIGENT JOB HANDLING:
When users ask about jobs, be SMART and CONTEXTUAL about their request:

IF USER HAS MEANINGFUL PREFERENCES (has job_roles, locations, or other key fields):
Acknowledge their job request and give them options:
"🔥 Looking for jobs? You can:
• Send 'menu' and select 'Show Jobs' to see current matches
• Update preferences for different jobs
• You'll also get instant alerts when new matching jobs are found!"

IF USER HAS NO MEANINGFUL PREFERENCES (empty or minimal preferences):
"🎯 To find [job type] jobs, type 'menu' and select 'Change Preferences' to set up your profile first!"

ALWAYS acknowledge what they're asking for and be helpful about their specific request.

KEEP RESPONSES SHORT BUT ENERGETIC:
- Be helpful but not wordy
- Focus on ACTION with excitement
- Use emojis to show enthusiasm

NATURAL RESPONSES:
- Greetings (hi, hello, hey): ENTHUSIASTIC response showing what you can do (see examples above)
- Job search requests: Use INTELLIGENT JOB HANDLING above based on user's preference status
- CV requests: "📋 Type 'menu' and select 'CV Analyzer' for professional CV review!"
- Salary questions: "💰 For [role] in Lagos: ₦X-₊Y monthly. Want specific tips?"
- Interview help: "🎤 Type 'menu' and select 'Interview Assistant' for interview preparation!"
- General chat: Keep it brief, friendly, helpful and energetic












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

    def _is_job_request(self, user_message: str) -> bool:
        """Check if user message is asking about jobs"""
        job_keywords = [
            "job",
            "jobs",
            "work",
            "employment",
            "position",
            "role",
            "opportunity",
            "opportunities",
            "vacancy",
            "vacancies",
            "hiring",
            "career",
            "opening",
            "openings",
        ]

        message_lower = user_message.lower()

        # Check for job-related keywords
        for keyword in job_keywords:
            if keyword in message_lower:
                return True

        return False

    def _has_meaningful_preferences(self, user_prefs: dict) -> bool:
        """Check if user has meaningful preferences set (regardless of confirmation status)"""
        if not user_prefs:
            return False

        # Check for key preference fields that indicate user has set up their profile
        meaningful_fields = [
            "job_roles",
            "preferred_locations",
            "work_arrangements",
            "years_of_experience",
            "salary_min",
        ]

        for field in meaningful_fields:
            value = user_prefs.get(field)
            if value is not None:
                # For lists, check if not empty
                if isinstance(value, list) and len(value) > 0:
                    return True
                # For non-lists, check if not empty/zero
                elif not isinstance(value, list) and value:
                    return True

        return False

    def _handle_job_request(
        self, user_message: str, user_preferences: dict, user_name: str = None
    ) -> str:
        """Handle job requests with explicit preference checking"""
        # Extract job type from message if mentioned
        job_type = self._extract_job_type(user_message)

        # Make responses more natural and action-oriented
        message_lower = user_message.lower()

        if self._has_meaningful_preferences(user_preferences):
            # User has preferences - be more direct and helpful
            if "new" in message_lower:
                return f"Ready to find {job_type + ' ' if job_type else ''}jobs? Type 'menu' and select 'Show Jobs' to see the latest opportunities!"
            else:
                return f"Let me help you find {job_type + ' ' if job_type else ''}jobs! Type 'menu' and select 'Show Jobs' to see current matches."
        else:
            # New user with no preferences - be encouraging and direct
            if job_type:
                return f"I'd love to help you find {job_type} jobs! First, type 'menu' and select 'Change Preferences' to set up your profile - it takes just 2 minutes!"
            else:
                return "I can help you find great jobs! Type 'menu' and select 'Change Preferences' to set up your profile first - it's quick and easy!"

    def _extract_job_type(self, user_message: str) -> str:
        """Extract job type from user message"""
        message_lower = user_message.lower()

        # Common job type patterns
        job_patterns = {
            "pm": "project management",
            "project management": "project management",
            "product management": "product management",
            "software": "software development",
            "developer": "development",
            "marketing": "marketing",
            "sales": "sales",
            "cybersecurity": "cybersecurity",
            "data": "data analysis",
            "hr": "human resources",
        }

        for pattern, job_type in job_patterns.items():
            if pattern in message_lower:
                return job_type

        return ""

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
