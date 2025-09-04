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

        return f"""You are Aremu, a helpful Nigerian job search assistant. You're professional, friendly, and focused on helping people find great job opportunities. Keep responses concise and actionable.

USER PROFILE:
- Name: {user_name or "there"}
- Job Preferences: {user_preferences}

PERSONALITY: Professional, helpful, friendly, and concise. Be warm but not overly enthusiastic.

GREETING RESPONSES (hi, hello, hey, good morning, etc.):
Be welcoming and show what you can do. Examples:
"Hi {user_name or 'there'}! I'm Aremu, your job search assistant. I can help you find jobs, review your CV, and prepare for interviews. What would you like to do today?"

"Hello {user_name or 'there'}! I'm here to help with your job search. I can find job opportunities, analyze your CV, and help you prepare for interviews. How can I assist you?"

"Good to see you, {user_name or 'there'}! I can help you find job matches, review your CV, and prepare for interviews. What would you like to work on?"

KEY PRIORITY - INTELLIGENT JOB HANDLING:
When users ask about jobs, be helpful and contextual about their request:

IF USER HAS MEANINGFUL PREFERENCES (has job_roles, locations, or other key fields):
Acknowledge their job request and give them options:
"Looking for jobs? You can:
• Type 'menu' and select 'Show Jobs' to see current matches
• Update preferences for different opportunities
• You'll get alerts when new matching jobs are found"

IF USER HAS NO MEANINGFUL PREFERENCES (empty or minimal preferences):
"To find [job type] jobs, type 'menu' and select 'Change Preferences' to set up your profile first."

ALWAYS acknowledge what they're asking for and be helpful about their specific request.

KEEP RESPONSES CONCISE AND HELPFUL:
- Be professional but friendly
- Focus on clear actions
- Use emojis sparingly for clarity

NATURAL RESPONSES:
- Greetings (hi, hello, hey): Friendly response showing what you can do (see examples above)
- Job search requests: Use INTELLIGENT JOB HANDLING above based on user's preference status
- CV requests: "I can help with CV review. Type 'menu' and select 'CV Analyzer' for professional feedback."
- Salary questions: "For [role] in Lagos: ₦X-₦Y monthly typically. Would you like specific salary insights?"
- Interview help: "I can help with interview prep. Type 'menu' and select 'Interview Assistant'."
- General chat: Keep it brief, friendly, and helpful












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

                # Apply AI expansion to job roles if present
                if preferences.get("job_roles"):
                    expanded_preferences = self.expand_job_categories_with_ai(
                        preferences
                    )
                    preferences.update(expanded_preferences)

                # Apply AI standardization to locations if present
                if preferences.get("preferred_locations"):
                    standardized_preferences = self.standardize_locations_with_ai(
                        preferences
                    )
                    preferences.update(standardized_preferences)

                logger.info(f"🤖 LLM parsed preferences: {preferences}")
                return preferences
            else:
                logger.error(f"❌ No JSON in LLM response: {result}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error parsing preferences with LLM: {e}")
            return {}

    def expand_job_categories_with_ai(self, preferences: Dict) -> Dict:
        """Use AI to expand job categories when user sets job preferences"""
        try:
            job_roles = preferences.get("job_roles", [])
            if not job_roles:
                return {}

            # Create AI prompt for job category expansion
            expansion_prompt = f"""You are an expert job market analyst. A user mentioned these job interests: {', '.join(job_roles)}

Based on their input, generate 5 standardized job categories and related roles that fit their interests. This will help them discover more relevant job opportunities.

Return ONLY a JSON object with these fields:

{{
  "expanded_job_roles": ["5 standardized job titles that match their interests"],
  "job_categories": ["3-5 industry categories that fit these roles"]
}}

EXAMPLES:
- If user says "sales" → expanded_job_roles: ["Sales Representative", "Business Development Manager", "Account Manager", "Sales Executive", "Customer Success Manager"]
- If user says "developer" → expanded_job_roles: ["Software Developer", "Frontend Developer", "Backend Developer", "Full Stack Developer", "Mobile Developer"]
- If user says "marketing" → expanded_job_roles: ["Digital Marketing Specialist", "Marketing Manager", "Content Marketing Manager", "Social Media Manager", "Marketing Coordinator"]

RULES:
- Generate exactly 5 standardized job roles
- Include 3-5 relevant industry categories
- Focus on Nigerian job market context
- Make roles specific and searchable
- Return valid JSON only

JSON:"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": expansion_prompt}],
                max_tokens=400,
                temperature=0.3,
            )

            result = response.choices[0].message.content.strip()

            # Parse JSON response
            import json

            if "{" in result and "}" in result:
                start = result.find("{")
                end = result.rfind("}") + 1
                json_str = result[start:end]
                expanded_data = json.loads(json_str)

                # Combine original and expanded job roles (remove duplicates)
                original_roles = set(role.lower() for role in job_roles)
                expanded_roles = expanded_data.get("expanded_job_roles", [])

                # Add expanded roles that aren't already present
                final_roles = job_roles.copy()
                for role in expanded_roles:
                    if role.lower() not in original_roles:
                        final_roles.append(role)

                logger.info(
                    f"🚀 AI expanded job roles from {len(job_roles)} to {len(final_roles)}"
                )
                logger.info(
                    f"🎯 Added job categories: {expanded_data.get('job_categories', [])}"
                )

                return {
                    "job_roles": final_roles,
                    "job_categories": expanded_data.get("job_categories", []),
                }
            else:
                logger.error(f"❌ No JSON in AI expansion response: {result}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error expanding job categories with AI: {e}")
            return {}

    def standardize_locations_with_ai(self, preferences: Dict) -> Dict:
        """Use AI to standardize location preferences for better matching"""
        try:
            locations = preferences.get("preferred_locations", [])
            if not locations:
                return {}

            # Create AI prompt for location standardization
            standardization_prompt = f"""You are an expert on Nigerian geography and job markets. A user mentioned these location preferences: {', '.join(locations)}

Standardize these locations for better job matching. Focus on:
1. Correcting spelling and formatting
2. Using standard city/state names
3. Handling common abbreviations
4. Adding relevant nearby areas if appropriate
5. Keeping "Remote" as-is if mentioned

Return ONLY a JSON object with this field:

{{
  "standardized_locations": ["list of 3-5 standardized location names"]
}}

EXAMPLES:
- Input: ["lagos", "abj"] → Output: ["Lagos", "Abuja"]
- Input: ["portharcourt", "warri"] → Output: ["Port Harcourt", "Warri", "Rivers State", "Delta State"]
- Input: ["remote", "lagos"] → Output: ["Remote", "Lagos", "Lagos State"]
- Input: ["kano"] → Output: ["Kano", "Kano State", "Northern Nigeria"]

RULES:
- Use proper capitalization (Lagos, not lagos)
- Include state names for major cities
- Keep "Remote", "Hybrid" as-is
- Add regional context for smaller cities
- Maximum 5 locations
- Focus on Nigerian locations
- Return valid JSON only

JSON:"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": standardization_prompt}],
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
                standardized_data = json.loads(json_str)

                standardized_locations = standardized_data.get(
                    "standardized_locations", []
                )

                if standardized_locations:
                    logger.info(
                        f"📍 AI standardized locations from {locations} to {standardized_locations}"
                    )

                    return {"preferred_locations": standardized_locations}
                else:
                    logger.warning("⚠️ No standardized locations returned")
                    return {}
            else:
                logger.error(f"❌ No JSON in AI standardization response: {result}")
                return {}

        except Exception as e:
            logger.error(f"❌ Error standardizing locations with AI: {e}")
            return {}
