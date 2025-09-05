#!/usr/bin/env python3
"""
Flexible User Preference Manager - Allows any job title while providing intelligent suggestions
"""

import logging
from typing import Dict, List, Optional, Union
import re

logger = logging.getLogger(__name__)


class FlexiblePreferenceManager:
    """Flexible preference manager that accepts any job title while providing intelligent categorization"""

    # SUGGESTED job categories (not enforced)
    SUGGESTED_JOB_CATEGORIES = {
        "technology",
        "healthcare",
        "education",
        "finance",
        "marketing",
        "sales",
        "design",
        "operations",
        "human resources",
        "legal",
        "customer service",
        "hospitality",
        "construction",
        "manufacturing",
        "media",
        "consulting",
        "government",
        "non-profit",
        "retail",
        "transportation",
        "real estate",
    }

    # SUGGESTED work arrangements
    VALID_WORK_ARRANGEMENTS = {"remote", "hybrid", "on-site"}

    # SUGGESTED employment types
    VALID_EMPLOYMENT_TYPES = {
        "full-time",
        "part-time",
        "contract",
        "internship",
        "freelance",
        "temporary",
        "volunteer",
    }

    # SUGGESTED experience levels
    VALID_EXPERIENCE_LEVELS = {"entry", "junior", "mid", "senior", "lead", "executive"}

    # SUGGESTED currencies
    VALID_CURRENCIES = {"USD", "NGN", "EUR", "GBP", "CAD", "AUD"}

    # SUGGESTED salary periods
    VALID_SALARY_PERIODS = {"hourly", "daily", "weekly", "monthly", "yearly"}

    # INTELLIGENT JOB TITLE CATEGORIZATION (for suggestions)
    JOB_TITLE_PATTERNS = {
        "technology": [
            r"developer",
            r"engineer",
            r"programmer",
            r"architect",
            r"analyst",
            r"react",
            r"vue",
            r"angular",
            r"node",
            r"python",
            r"java",
            r"javascript",
            r"frontend",
            r"backend",
            r"fullstack",
            r"mobile",
            r"web",
            r"software",
            r"devops",
            r"qa",
            r"testing",
            r"cybersecurity",
            r"data",
            r"ai",
            r"ml",
        ],
        "healthcare": [
            r"nurse",
            r"doctor",
            r"physician",
            r"therapist",
            r"medical",
            r"health",
            r"pharmacist",
            r"dentist",
            r"surgeon",
            r"radiologist",
            r"technician",
        ],
        "education": [
            r"teacher",
            r"professor",
            r"instructor",
            r"tutor",
            r"educator",
            r"lecturer",
            r"coordinator",
            r"administrator",
            r"principal",
        ],
        "finance": [
            r"accountant",
            r"analyst",
            r"banker",
            r"advisor",
            r"auditor",
            r"financial",
            r"investment",
            r"credit",
            r"tax",
            r"bookkeeper",
        ],
        "marketing": [
            r"marketing",
            r"marketer",
            r"seo",
            r"content",
            r"social media",
            r"brand",
            r"digital",
            r"campaign",
            r"advertising",
        ],
        "sales": [
            r"sales",
            r"account manager",
            r"business development",
            r"representative",
            r"consultant",
            r"relationship",
            r"client",
        ],
        "design": [
            r"designer",
            r"design",
            r"creative",
            r"artist",
            r"ui",
            r"ux",
            r"graphic",
            r"web design",
            r"product design",
            r"visual",
        ],
    }

    def __init__(self, db_connection):
        self.connection = db_connection

    def validate_and_standardize(self, raw_preferences: Dict) -> Dict:
        """Flexible validation that accepts any job title while providing intelligent standardization"""
        try:
            standardized = {}

            # JOB ROLES - Accept ANY job title (no restrictions)
            if (
                "job_type" in raw_preferences
                or "job_role" in raw_preferences
                or "job_roles" in raw_preferences
            ):
                job_input = (
                    raw_preferences.get("job_type")
                    or raw_preferences.get("job_role")
                    or raw_preferences.get("job_roles")
                )
                roles = self._standardize_job_roles_flexible(job_input)
                if roles:
                    standardized["job_roles"] = roles
                    # Auto-infer categories from roles
                    inferred_categories = self._infer_categories_from_roles_flexible(
                        roles
                    )
                    if inferred_categories:
                        standardized["job_categories"] = inferred_categories

            # JOB CATEGORIES - Accept any category but suggest standard ones
            if "job_category" in raw_preferences:
                categories = self._standardize_job_categories_flexible(
                    raw_preferences["job_category"]
                )
                if categories:
                    standardized["job_categories"] = categories

            # WORK ARRANGEMENTS - Validate against known types
            if (
                "work_arrangement" in raw_preferences
                or "location_preference" in raw_preferences
                or "work_arrangements" in raw_preferences
            ):
                work_input = (
                    raw_preferences.get("work_arrangement")
                    or raw_preferences.get("location_preference")
                    or raw_preferences.get("work_arrangements")
                )
                arrangements = self._standardize_work_arrangements(work_input)
                if arrangements:
                    standardized["work_arrangements"] = arrangements

            # EMPLOYMENT TYPES - Validate against known types
            if "employment_type" in raw_preferences:
                emp_types = self._standardize_employment_types(
                    raw_preferences["employment_type"]
                )
                if emp_types:
                    standardized["employment_types"] = emp_types

            # EXPERIENCE LEVEL - Validate against known levels
            if "experience_level" in raw_preferences:
                exp_level = self._standardize_experience_level(
                    raw_preferences["experience_level"]
                )
                if exp_level:
                    standardized["experience_level"] = exp_level

            # YEARS OF EXPERIENCE - Accept any reasonable number
            if "years_of_experience" in raw_preferences:
                years = self._standardize_years_experience(
                    raw_preferences["years_of_experience"]
                )
                if years is not None:
                    standardized["years_of_experience"] = years

            # SALARY PREFERENCES - Validate currency but accept any amount
            if "salary_currency" in raw_preferences:
                currency = self._standardize_currency(
                    raw_preferences["salary_currency"]
                )
                if currency:
                    standardized["salary_currency"] = currency

            if "salary_period" in raw_preferences:
                period = self._standardize_salary_period(
                    raw_preferences["salary_period"]
                )
                if period:
                    standardized["salary_period"] = period

            for field in ["salary_min", "salary_max"]:
                if field in raw_preferences:
                    try:
                        value = int(raw_preferences[field])
                        if value > 0:
                            standardized[field] = value
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid {field}: {raw_preferences[field]}")

            # LOCATION PREFERENCES - Accept any location
            if (
                "location" in raw_preferences
                or "preferred_location" in raw_preferences
                or "preferred_locations" in raw_preferences
            ):
                location_input = (
                    raw_preferences.get("location")
                    or raw_preferences.get("preferred_location")
                    or raw_preferences.get("preferred_locations")
                )
                locations = self._standardize_locations_flexible(location_input)
                if locations:
                    standardized["preferred_locations"] = locations

            # SKILLS - Accept any skills
            if "skills" in raw_preferences:
                skills = self._standardize_skills_flexible(raw_preferences["skills"])
                if skills:
                    standardized["technical_skills"] = skills

            # LANGUAGES - Accept any languages
            if "languages" in raw_preferences or "languages_spoken" in raw_preferences:
                lang_input = raw_preferences.get("languages") or raw_preferences.get(
                    "languages_spoken"
                )
                languages = self._standardize_languages_flexible(lang_input)
                if languages:
                    standardized["languages_spoken"] = languages

            # BOOLEAN FIELDS
            for field in ["salary_negotiable", "willing_to_relocate"]:
                if field in raw_preferences:
                    standardized[field] = bool(raw_preferences[field])

            logger.info(f"✅ Flexible standardization: {standardized}")
            return standardized

        except Exception as e:
            logger.error(f"❌ Error in flexible validation: {e}")
            return {}

    def _standardize_job_roles_flexible(
        self, role_input: Union[str, List[str]]
    ) -> List[str]:
        """Accept ANY job role and expand using AI to generate related roles"""
        if isinstance(role_input, str):
            if "," in role_input:
                roles = [role.strip().lower() for role in role_input.split(",")]
            else:
                roles = [role_input.strip().lower()]
        elif isinstance(role_input, list):
            roles = [str(role).strip().lower() for role in role_input]
        else:
            return []

        # Clean and format roles first
        clean_roles = []
        for role in roles:
            if role and len(role) > 1:
                # Basic cleaning
                clean_role = re.sub(
                    r"[^\w\s\-\+\.]", "", role
                )  # Remove special chars except dash, plus, dot
                clean_role = re.sub(
                    r"\s+", " ", clean_role
                ).strip()  # Normalize whitespace
                if clean_role:
                    clean_roles.append(clean_role)

        # Use AI to expand job roles for better matching
        expanded_roles = []
        for role in clean_roles:
            ai_expanded = self._ai_expand_job_role(role)
            if ai_expanded:
                expanded_roles.extend(ai_expanded)
            else:
                # Fallback to original role if AI expansion fails
                expanded_roles.append(role)

        # Remove duplicates while preserving order
        seen = set()
        final_roles = []
        for role in expanded_roles:
            if role.lower() not in seen:
                seen.add(role.lower())
                final_roles.append(role)

        return final_roles

    def _ai_expand_job_role(self, role: str) -> List[str]:
        """Use AI to expand a single job role into multiple related roles"""
        try:
            import openai
            import os

            # Get OpenAI API key
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("No OpenAI API key found for job role expansion")
                return [role]

            client = openai.OpenAI(api_key=api_key)

            prompt = f"""Given the job role "{role}", generate 5 standardized, specific job titles that are related and commonly used in Nigeria.

Requirements:
- Include the original role if it's already well-formatted
- Focus on Nigerian job market terminology
- Include different seniority levels where appropriate
- Make titles specific and searchable
- Return only the job titles, one per line
- No numbering, bullets, or extra text

Example for "sales":
Sales Representative
Sales Manager
Business Development Executive
Account Manager
Sales Coordinator

Job role to expand: {role}"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3,
            )

            if response.choices and response.choices[0].message.content:
                expanded_roles = []
                lines = response.choices[0].message.content.strip().split("\n")

                for line in lines:
                    clean_line = line.strip()
                    # Remove numbering, bullets, etc.
                    clean_line = re.sub(r"^[\d\.\-\*\+\s]+", "", clean_line)
                    if clean_line and len(clean_line) > 2:
                        expanded_roles.append(clean_line)

                if expanded_roles:
                    logger.info(
                        f"✅ AI expanded '{role}' to {len(expanded_roles)} roles: {expanded_roles}"
                    )
                    return expanded_roles[:5]  # Limit to 5 roles

        except Exception as e:
            logger.warning(f"AI expansion failed for '{role}': {e}")

        # Fallback to original role
        return [role]

    def _infer_categories_from_roles_flexible(self, roles: List[str]) -> List[str]:
        """Intelligently infer job categories from any job title using pattern matching"""
        categories = set()

        for role in roles:
            role_lower = role.lower()

            # Check each category's patterns
            for category, patterns in self.JOB_TITLE_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, role_lower):
                        categories.add(category)
                        break  # Found a match for this category

        return list(categories)

    def _standardize_job_categories_flexible(
        self, category_input: Union[str, List[str]]
    ) -> List[str]:
        """Accept any job category but suggest standard ones"""
        if isinstance(category_input, str):
            if "," in category_input:
                categories = [cat.strip().lower() for cat in category_input.split(",")]
            else:
                categories = [category_input.strip().lower()]
        elif isinstance(category_input, list):
            categories = [str(cat).strip().lower() for cat in category_input]
        else:
            return []

        # Clean categories but don't restrict them
        clean_categories = []
        for cat in categories:
            if cat and len(cat) > 1:
                clean_cat = re.sub(
                    r"[^\w\s\-]", "", cat
                )  # Remove special chars except dash
                clean_cat = re.sub(
                    r"\s+", " ", clean_cat
                ).strip()  # Normalize whitespace
                if clean_cat:
                    clean_categories.append(clean_cat)

        return clean_categories

    def _standardize_locations_flexible(
        self, location_input: Union[str, List[str]]
    ) -> List[str]:
        """Accept any location"""
        if isinstance(location_input, str):
            if "," in location_input:
                locations = [loc.strip().title() for loc in location_input.split(",")]
            else:
                locations = [location_input.strip().title()]
        elif isinstance(location_input, list):
            locations = [str(loc).strip().title() for loc in location_input]
        else:
            return []

        # Clean locations
        clean_locations = []
        for loc in locations:
            if loc and len(loc) > 1:
                clean_locations.append(loc)

        return clean_locations

    def _standardize_skills_flexible(
        self, skills_input: Union[str, List[str]]
    ) -> List[str]:
        """Accept any skills"""
        if isinstance(skills_input, str):
            if "," in skills_input:
                skills = [s.strip().title() for s in skills_input.split(",")]
            else:
                skills = [skills_input.strip().title()]
        elif isinstance(skills_input, list):
            skills = [str(s).strip().title() for s in skills_input]
        else:
            return []

        # Filter out empty and very short skills
        return [s for s in skills if s and len(s) > 1]

    def _standardize_languages_flexible(
        self, lang_input: Union[str, List[str]]
    ) -> List[str]:
        """Accept any languages"""
        if isinstance(lang_input, str):
            if "," in lang_input:
                languages = [lang.strip().title() for lang in lang_input.split(",")]
            else:
                languages = [lang_input.strip().title()]
        elif isinstance(lang_input, list):
            languages = [str(lang).strip().title() for lang in lang_input]
        else:
            return []

        return [lang for lang in languages if lang and len(lang) > 1]

    # Add the missing standardization methods from the enhanced manager
    def _standardize_work_arrangements(
        self, arrangement_input: Union[str, List[str]]
    ) -> List[str]:
        """Standardize work arrangements"""
        if isinstance(arrangement_input, list):
            # Handle list input (from guided setup and update form)
            valid_arrangements = []
            for arrangement in arrangement_input:
                if isinstance(arrangement, str):
                    clean_arrangement = arrangement.strip().lower()
                    # Map title case to lowercase enum values
                    arrangement_map = {
                        "remote": "remote",
                        "onsite": "on-site",
                        "hybrid": "hybrid",
                    }
                    mapped_arrangement = arrangement_map.get(
                        clean_arrangement, clean_arrangement
                    )
                    if mapped_arrangement in self.VALID_WORK_ARRANGEMENTS:
                        valid_arrangements.append(mapped_arrangement)
            return valid_arrangements

        elif isinstance(arrangement_input, str):
            arrangement = arrangement_input.strip().lower()

            # Map variations
            arrangement_map = {
                "remote": "remote",
                "work from home": "remote",
                "wfh": "remote",
                "hybrid": "hybrid",
                "flexible": "hybrid",
                "on-site": "on-site",
                "onsite": "on-site",
                "office": "on-site",
                "in-person": "on-site",
            }

            standardized = arrangement_map.get(arrangement, arrangement)
            if standardized in self.VALID_WORK_ARRANGEMENTS:
                return [standardized]

        return []

    def _standardize_employment_types(
        self, emp_input: Union[str, List[str]]
    ) -> List[str]:
        """Standardize employment types"""
        if isinstance(emp_input, str):
            if "," in emp_input:
                emp_types = [et.strip().lower() for et in emp_input.split(",")]
            else:
                emp_types = [emp_input.strip().lower()]
        elif isinstance(emp_input, list):
            emp_types = [str(et).strip().lower() for et in emp_input]
        else:
            return []

        # Map variations
        emp_map = {
            "full-time": "full-time",
            "fulltime": "full-time",
            "ft": "full-time",
            "part-time": "part-time",
            "parttime": "part-time",
            "pt": "part-time",
            "contract": "contract",
            "contractor": "contract",
            "consulting": "contract",
            "internship": "internship",
            "intern": "internship",
            "freelance": "freelance",
            "freelancer": "freelance",
            "temporary": "temporary",
            "temp": "temporary",
            "volunteer": "volunteer",
            "volunteering": "volunteer",
        }

        valid_types = []
        for et in emp_types:
            standardized = emp_map.get(et, et)
            if standardized in self.VALID_EMPLOYMENT_TYPES:
                valid_types.append(standardized)

        return valid_types

    def _standardize_experience_level(self, exp_input: str) -> Optional[str]:
        """Standardize experience level"""
        if not exp_input:
            return None

        exp = exp_input.strip().lower()

        # Map variations
        exp_map = {
            "entry": "entry",
            "entry-level": "entry",
            "beginner": "entry",
            "fresh": "entry",
            "junior": "junior",
            "jr": "junior",
            "mid": "mid",
            "middle": "mid",
            "intermediate": "mid",
            "mid-level": "mid",
            "senior": "senior",
            "sr": "senior",
            "senior-level": "senior",
            "lead": "lead",
            "team lead": "lead",
            "tech lead": "lead",
            "principal": "lead",
            "executive": "executive",
            "director": "executive",
            "vp": "executive",
            "cto": "executive",
        }

        standardized = exp_map.get(exp, exp)
        if standardized in self.VALID_EXPERIENCE_LEVELS:
            return standardized

        logger.warning(f"Invalid experience level: {exp_input}")
        return None

    def _standardize_years_experience(
        self, years_input: Union[str, int]
    ) -> Optional[int]:
        """Standardize years of experience"""
        try:
            if isinstance(years_input, str):
                # Extract numbers from strings like "3 years", "5+ years"
                import re

                numbers = re.findall(r"\d+", years_input)
                if numbers:
                    years = int(numbers[0])
                else:
                    return None
            else:
                years = int(years_input)

            # Reasonable bounds
            if 0 <= years <= 50:
                return years
            else:
                logger.warning(f"Years of experience out of range: {years}")
                return None

        except (ValueError, TypeError):
            logger.warning(f"Invalid years of experience: {years_input}")
            return None

    def _standardize_currency(self, currency_input: str) -> Optional[str]:
        """Standardize currency"""
        if not currency_input:
            return None

        currency = currency_input.strip().upper()

        # Handle variations
        currency_map = {
            "DOLLAR": "USD",
            "DOLLARS": "USD",
            "$": "USD",
            "US DOLLAR": "USD",
            "NAIRA": "NGN",
            "₦": "NGN",
            "NIGERIAN NAIRA": "NGN",
            "EURO": "EUR",
            "€": "EUR",
            "EUROS": "EUR",
            "POUND": "GBP",
            "£": "GBP",
            "POUNDS": "GBP",
            "BRITISH POUND": "GBP",
            "CANADIAN DOLLAR": "CAD",
            "CAD": "CAD",
            "AUSTRALIAN DOLLAR": "AUD",
            "AUD": "AUD",
        }

        standardized = currency_map.get(currency, currency)
        if standardized in self.VALID_CURRENCIES:
            return standardized

        logger.warning(f"Invalid currency: {currency_input}")
        return None

    def _standardize_salary_period(self, period_input: str) -> Optional[str]:
        """Standardize salary period"""
        if not period_input:
            return None

        period = period_input.strip().lower()

        period_map = {
            "hour": "hourly",
            "hourly": "hourly",
            "per hour": "hourly",
            "day": "daily",
            "daily": "daily",
            "per day": "daily",
            "week": "weekly",
            "weekly": "weekly",
            "per week": "weekly",
            "month": "monthly",
            "monthly": "monthly",
            "per month": "monthly",
            "year": "yearly",
            "yearly": "yearly",
            "annual": "yearly",
            "annually": "yearly",
        }

        standardized = period_map.get(period, period)
        if standardized in self.VALID_SALARY_PERIODS:
            return standardized

        return "monthly"  # Default to monthly

    def _intelligent_merge_preferences(self, existing: Dict, new: Dict) -> Dict:
        """Intelligently merge new preferences with existing ones"""
        if not existing:
            return new

        merged = existing.copy()

        for field, new_value in new.items():
            if new_value is None:
                continue  # Skip None values

            if field in [
                "job_roles",
                "job_categories",
                "technical_skills",
                "preferred_locations",
            ]:
                # For arrays: intelligently merge (append unique items)
                existing_list = merged.get(field, []) or []
                if isinstance(new_value, list):
                    # Add new items that aren't already present
                    for item in new_value:
                        if item and item not in existing_list:
                            existing_list.append(item)
                    merged[field] = existing_list
                elif isinstance(new_value, str) and new_value not in existing_list:
                    existing_list.append(new_value)
                    merged[field] = existing_list

            elif field in ["salary_min", "salary_max"]:
                # For salary: take the new value if it's more specific
                if new_value and (
                    not merged.get(field) or new_value != merged.get(field)
                ):
                    merged[field] = new_value

            elif field in ["years_experience", "salary_currency", "salary_period"]:
                # For single values: update if new value is provided
                if new_value:
                    merged[field] = new_value

            else:
                # For other fields: update with new value
                merged[field] = new_value

        logger.info(
            f"🧠 Intelligent merge: {len(existing)} existing + {len(new)} new = {len(merged)} merged fields"
        )
        return merged

    def save_preferences(self, user_id: int, preferences: Dict) -> bool:
        """Intelligently save preferences to database with smart merging"""
        try:
            # Validate and standardize first
            clean_prefs = self.validate_and_standardize(preferences)

            if not clean_prefs:
                logger.warning(f"No valid preferences to save for user {user_id}")
                return False

            # SIMPLE REPLACE: Use new preferences directly (cleaner approach)
            merged_prefs = clean_prefs

            cursor = self.connection.cursor()

            # Build query using merged preferences
            fields = []
            values = []
            placeholders = []

            for field, value in merged_prefs.items():
                # Skip fields that are handled separately to avoid duplication
                if field in ["user_id", "created_at", "updated_at", "id"]:
                    continue

                fields.append(field)
                values.append(value)

                # Only cast enums for the standardized fields
                if field == "work_arrangements":
                    placeholders.append("%s::work_arrangement_enum[]")
                elif field == "employment_types":
                    placeholders.append("%s::employment_type_enum[]")
                elif field == "salary_currency":
                    placeholders.append("%s::currency_enum")
                elif field == "salary_period":
                    placeholders.append("%s::salary_period_enum")
                elif field == "experience_level":
                    placeholders.append("%s::experience_level_enum")
                else:
                    # TEXT arrays and other fields - no casting needed
                    placeholders.append("%s")

            # Add user_id
            fields.append("user_id")
            values.append(user_id)
            placeholders.append("%s")

            # Build conflict resolution
            update_fields = []
            for field in merged_prefs.keys():
                # Skip fields that are handled separately
                if field in ["user_id", "created_at", "updated_at", "id"]:
                    continue
                elif field == "work_arrangements":
                    update_fields.append(
                        f"{field} = EXCLUDED.{field}::work_arrangement_enum[]"
                    )
                elif field == "employment_types":
                    update_fields.append(
                        f"{field} = EXCLUDED.{field}::employment_type_enum[]"
                    )
                elif field == "salary_currency":
                    update_fields.append(f"{field} = EXCLUDED.{field}::currency_enum")
                elif field == "salary_period":
                    update_fields.append(
                        f"{field} = EXCLUDED.{field}::salary_period_enum"
                    )
                elif field == "experience_level":
                    update_fields.append(
                        f"{field} = EXCLUDED.{field}::experience_level_enum"
                    )
                else:
                    update_fields.append(f"{field} = EXCLUDED.{field}")

            query = f"""
                INSERT INTO user_preferences ({', '.join(fields)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (user_id)
                DO UPDATE SET
                    {', '.join(update_fields)},
                    updated_at = CURRENT_TIMESTAMP
            """

            cursor.execute(query, values)
            logger.info(
                f"💾 Saved flexible preferences for user {user_id}: {clean_prefs}"
            )
            return True

        except Exception as e:
            logger.error(
                f"❌ Error saving flexible preferences for user {user_id}: {e}"
            )
            return False

    def get_preferences(self, user_id: int) -> Dict:
        """Get user preferences from flexible schema"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT * FROM user_preferences WHERE user_id = %s", (user_id,)
            )
            result = cursor.fetchone()

            if result:
                # Convert to dict
                columns = [desc[0] for desc in cursor.description]
                prefs = dict(zip(columns, result))

                # Parse PostgreSQL arrays properly
                array_fields = [
                    "job_roles",
                    "job_categories",
                    "preferred_locations",
                    "technical_skills",
                    "work_arrangements",
                ]

                for field in array_fields:
                    if field in prefs and prefs[field]:
                        value = prefs[field]
                        if isinstance(value, str):
                            # Parse PostgreSQL array format: {item1,item2,item3}
                            if value.startswith("{") and value.endswith("}"):
                                # Remove braces and split by comma
                                items = value[1:-1].split(",")
                                # Clean up each item (remove quotes and whitespace)
                                prefs[field] = [
                                    item.strip().strip("\"'")
                                    for item in items
                                    if item.strip()
                                ]
                            else:
                                # Single item, convert to list
                                prefs[field] = [value.strip()]

                return prefs
            else:
                return {}

        except Exception as e:
            logger.error(
                f"❌ Error getting flexible preferences for user {user_id}: {e}"
            )
            return {}

    def clear_preferences(self, user_id: int) -> bool:
        """Clear all preferences for a user (for reset functionality)"""
        try:
            cursor = self.connection.cursor()

            # Delete existing preferences
            cursor.execute(
                "DELETE FROM user_preferences WHERE user_id = %s", (user_id,)
            )

            self.connection.commit()
            logger.info(f"🔄 Cleared preferences for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error clearing preferences: {e}")
            self.connection.rollback()
            return False
