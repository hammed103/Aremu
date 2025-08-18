#!/usr/bin/env python3
"""
Job Service - Handles job-related operations
Generates realistic job listings and manages job search
"""

import logging
from typing import Dict, List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from legacy.database_manager import DatabaseManager
from legacy.intelligent_job_matcher import IntelligentJobMatcher

logger = logging.getLogger(__name__)


class JobService:
    """Handles job search and listing generation"""

    def __init__(self):
        """Initialize the job service with database connection and intelligent matcher"""
        self.db = DatabaseManager()
        self.db.connect()
        self.intelligent_matcher = IntelligentJobMatcher(self.db.connection)
        logger.info(
            "✅ Job Service initialized with database connection and intelligent matcher"
        )

    def generate_realistic_job_listings(
        self,
        user_preferences: Dict,
        user_name: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> List[str]:
        """Get real job listings from database - returns list of individual job messages"""
        try:
            job_roles = user_preferences.get("job_roles", [])

            if not job_roles:
                return [
                    "I need to know what type of job you're looking for. Please type 'settings' to add your job title (e.g., 'Software Developer', 'Project Manager', etc.)."
                ]

            # Use the provided user ID or create a temporary one
            if not user_id:
                temp_phone = "+temp_search_user"
                user_id = self.db.get_or_create_user(temp_phone, "Search User")

            # Get list of jobs already shown to this user
            shown_job_ids = self._get_shown_job_ids(user_id)

            # Use intelligent matcher for AI-powered job matching
            all_jobs = self.intelligent_matcher.search_jobs_for_user(user_id, limit=10)

            # Filter out jobs already shown to user and apply minimum match score
            jobs = []
            for job in all_jobs:
                job_id = job.get("id")
                match_score = job.get("match_score", 0)

                # Only include jobs with 35%+ match and not already shown
                if job_id not in shown_job_ids and match_score >= 35.0:
                    jobs.append(job)
                    if len(jobs) >= 3:  # Only need 3 jobs
                        break

            if not jobs:
                # Check if user has been shown jobs before
                if shown_job_ids:
                    return [
                        "🎉 You're all caught up! No new jobs matching your preferences so far. You'll get instant alerts as soon as new opportunities become available!"
                    ]
                else:
                    return [
                        f"No jobs found for {', '.join(job_roles)} at the moment. We'll notify you when new opportunities become available!"
                    ]

            # Format jobs using ai_summary - one message per job (legacy delivery style)
            job_messages = []

            # First message: Introduction
            intro_msg = f"Found 3+ jobs matching your preferences. Here's the top 3:"
            job_messages.append(intro_msg)

            # Individual job messages using ai_summary
            for i, job in enumerate(jobs, 1):
                job_message = self._format_single_job_with_ai_summary(job, i)
                job_messages.append(job_message)

            # Add follow-up message to encourage more job requests
            follow_up_message = "💬 Type 'jobs' again to see more recent opportunities!"
            job_messages.append(follow_up_message)

            # Track that these jobs have been shown to the user
            self._save_shown_jobs(
                user_id, [job.get("id") for job in jobs if job.get("id")]
            )

            return job_messages

        except Exception as e:
            logger.error(f"❌ Error getting real job listings: {e}")
            return [
                "🔍 I'm searching for jobs that match your preferences. Please try again in a moment."
            ]

    def _get_salary_range(self, experience: int, salary_min: int) -> tuple:
        """Determine experience level and salary ranges"""
        if experience <= 1:
            level = "Entry-level"
            salary_range_low = max(salary_min, 300000)
            salary_range_high = salary_range_low + 200000
        elif experience <= 3:
            level = "Junior"
            salary_range_low = max(salary_min, 450000)
            salary_range_high = salary_range_low + 300000
        elif experience <= 6:
            level = "Mid-level"
            salary_range_low = max(salary_min, 700000)
            salary_range_high = salary_range_low + 500000
        else:
            level = "Senior"
            salary_range_low = max(salary_min, 1200000)
            salary_range_high = salary_range_low + 800000

        return level, salary_range_low, salary_range_high

    def _get_realistic_companies(self, primary_role: str) -> List[tuple]:
        """Get realistic company names based on role"""
        if "developer" in primary_role.lower() or "engineer" in primary_role.lower():
            return [
                ("TechStart Lagos", "Hybrid - 3 days office"),
                ("FinTech Plus", "Remote"),
                ("Digital Solutions Hub", "Lagos/Remote Hybrid"),
            ]
        elif "marketing" in primary_role.lower():
            return [
                ("Brand Masters Agency", "Lagos (Hybrid)"),
                ("Digital Growth Co", "Remote"),
                ("Marketing Hub Nigeria", "Lagos/Abuja"),
            ]
        elif "sales" in primary_role.lower():
            return [
                ("Sales Excellence Ltd", "Lagos (Field work)"),
                ("Business Growth Partners", "Remote + Travel"),
                ("Revenue Builders", "Lagos/Port Harcourt"),
            ]
        elif "data" in primary_role.lower() or "analyst" in primary_role.lower():
            return [
                ("Data Insights Nigeria", "Remote"),
                ("Analytics Pro", "Lagos (Hybrid)"),
                ("Business Intelligence Hub", "Lagos/Remote"),
            ]
        else:
            return [
                ("Professional Services Ltd", "Lagos"),
                ("Business Solutions Co", "Remote"),
                ("Corporate Excellence", "Lagos/Abuja"),
            ]

    def _get_job_requirements(self, primary_role: str, job_number: int) -> str:
        """Get job requirements based on role and job number"""
        if "developer" in primary_role.lower() or "engineer" in primary_role.lower():
            requirements = [
                "React, JavaScript, HTML/CSS",
                "Python, API integration, Django",
                "Vue.js, responsive design, Git",
            ]
        elif "marketing" in primary_role.lower():
            requirements = [
                "Digital campaigns, Google Analytics",
                "Social media, content creation, SEO",
                "Email marketing, CRM, lead generation",
            ]
        elif "sales" in primary_role.lower():
            requirements = [
                "Client relationships, CRM, presentations",
                "Lead generation, negotiation, B2B sales",
                "Business development, market research",
            ]
        elif "data" in primary_role.lower() or "analyst" in primary_role.lower():
            requirements = [
                "Excel, SQL, Power BI",
                "Python, data visualization, statistics",
                "Business intelligence, reporting, dashboards",
            ]
        else:
            requirements = [
                "Professional communication, MS Office",
                "Team collaboration, project management",
                "Problem solving, analytical thinking",
            ]

        return (
            requirements[job_number - 1]
            if job_number <= len(requirements)
            else requirements[0]
        )

    def _get_experience_requirement(self, experience: int) -> str:
        """Get experience requirement text"""
        if experience <= 1:
            return "Fresh graduates welcome"
        elif experience <= 2:
            return f"{experience}-{experience+1} years experience"
        else:
            return f"{experience}+ years experience"

    def get_detailed_job_info(self, job_number: int, user_preferences: Dict) -> str:
        """Get detailed information for a specific job"""
        try:
            job_roles = user_preferences.get("job_roles", [])
            primary_role = job_roles[0] if job_roles else "Professional"

            # Sample detailed job information
            companies = self._get_realistic_companies(primary_role)
            if job_number <= len(companies):
                company, work_style = companies[job_number - 1]

                return f"""🏢 **Company:** {company}
📍 **Location:** Lagos with {work_style.lower()} flexibility
💰 **Salary:** Competitive package + benefits
⏱️ **Experience:** Perfect for your background

📋 **Key Responsibilities:**
• Lead projects and collaborate with cross-functional teams
• Develop and implement strategic initiatives
• Analyze data and provide insights for decision making
• Mentor junior team members and drive best practices

🎯 **Requirements:**
• Relevant degree or equivalent experience
• Strong analytical and communication skills
• Proficiency in relevant tools and technologies
• Team leadership and project management experience

💼 **Benefits:**
• Health insurance for family
• Annual performance bonus
• Professional development budget
• Flexible working arrangements

📧 **How to Apply:**
Send your CV and cover letter to: careers@{company.lower().replace(' ', '')}.com.ng
Subject: "{primary_role} Application - [Your Name]"
Mention you found this through Aremu Job Bot!

Would you like me to help you tailor your application?"""
            else:
                return "Please select a valid job number (1, 2, or 3)."

        except Exception as e:
            logger.error(f"❌ Error getting detailed job info: {e}")
            return "I'm having trouble getting the job details. Please try again."

    def _get_shown_job_ids(self, user_id: int) -> List[int]:
        """Get list of job IDs already shown to this user"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute(
                "SELECT job_id FROM user_job_history WHERE user_id = %s AND message_sent = TRUE",
                (user_id,),
            )
            results = cursor.fetchall()
            return [row[0] for row in results if row[0] is not None]
        except Exception as e:
            logger.error(f"❌ Error getting shown job IDs: {e}")
            return []

    def _save_shown_jobs(self, user_id: int, job_ids: List[int]) -> None:
        """Save job IDs that have been shown to the user"""
        try:
            if not job_ids:
                return

            cursor = self.db.connection.cursor()
            for job_id in job_ids:
                cursor.execute(
                    """
                    INSERT INTO user_job_history (user_id, job_id, shown_at, delivery_type, message_sent)
                    VALUES (%s, %s, NOW(), 'whatsapp', TRUE)
                    """,
                    (user_id, job_id),
                )
            self.db.connection.commit()
            logger.info(f"✅ Saved {len(job_ids)} shown jobs for user {user_id}")
        except Exception as e:
            logger.error(f"❌ Error saving shown jobs: {e}")
            # Don't fail the whole request if tracking fails
            pass

    def _format_job_with_ai_fields(self, job: Dict, index: int) -> str:
        """Enhanced job formatting using all AI fields"""
        try:
            # Extract core information
            title = job.get("title", "Job Opportunity")
            company = job.get("company", "Company")
            location = job.get("location", "Location")

            # Use AI-enhanced salary information
            ai_salary_min = job.get("ai_salary_min")
            ai_salary_max = job.get("ai_salary_max")
            ai_compensation = job.get("ai_compensation_summary")
            salary_min = job.get("salary_min")

            # Format salary display with AI enhancement
            if ai_salary_min and ai_salary_max:
                salary_display = f"💰 ₦{ai_salary_min:,} - ₦{ai_salary_max:,}"
            elif ai_salary_min:
                salary_display = f"💰 ₦{ai_salary_min:,}+"
            elif salary_min:
                salary_display = f"💰 ₦{salary_min:,}+"
            elif ai_compensation:
                salary_display = f"💰 {ai_compensation}"
            else:
                salary_display = "💰 Competitive salary"

            # Get AI-enhanced match information
            match_score = job.get("match_score", 0)
            match_reasons = job.get("match_reasons", [])

            # Use AI job function for better categorization
            ai_job_function = job.get("ai_job_function", "")
            ai_remote_allowed = job.get("ai_remote_allowed", False)

            # Build enhanced job listing
            job_listing = (
                f"*{index}. {title} - {company}*\n{salary_display}\n📍 {location}"
            )

            # Add remote work indicator
            if ai_remote_allowed:
                job_listing += " (Remote OK)"

            # Add match score and reasons
            if match_score > 0:
                job_listing += f"\n🎯 {match_score:.0f}% match"
                if match_reasons:
                    # Show top 2 match reasons
                    top_reasons = match_reasons[:2]
                    job_listing += f"\n✨ {', '.join(top_reasons)}"

            # Add AI job function if available
            if ai_job_function and ai_job_function.lower() not in title.lower():
                job_listing += f"\n🏷️ {ai_job_function}"

            return job_listing

        except Exception as e:
            logger.error(f"❌ Error formatting job with AI fields: {e}")
            # Fallback to basic formatting
            title = job.get("title", "Job Opportunity")
            company = job.get("company", "Company")
            match_score = job.get("match_score", 0)
            match_indicator = (
                f"🎯 {match_score:.0f}% match"
                if match_score > 0
                else "🎯 Real opportunity"
            )

            return f"*{index}. {title} - {company}*\n💰 Competitive salary\n📍 {job.get('location', 'Location')}\n{match_indicator}"

    def _format_single_job_with_ai_summary(self, job: Dict, index: int) -> str:
        """Format single job using ai_summary (legacy delivery style)"""
        try:
            match_score = job.get("match_score", 0)

            # Use AI summary if available (preferred method - like smart delivery engine)
            # The intelligent matcher renames ai_summary to whatsapp_summary
            ai_summary = job.get("whatsapp_summary") or job.get("ai_summary")
            if ai_summary:
                alert_msg = f"🚨 *JOB MATCH #{index}* ({match_score:.0f}% match)\n\n"
                alert_msg += ai_summary
                return alert_msg

            # Fallback formatting if no ai_summary
            title = job.get("title", "Job Opportunity")
            company = job.get("company", "Company")
            location = job.get("location", "Location")

            # Enhanced salary formatting
            ai_salary_min = job.get("ai_salary_min")
            ai_compensation = job.get("ai_compensation_summary")
            salary_min = job.get("salary_min")

            if ai_salary_min:
                salary_display = f"💰 ₦{ai_salary_min:,}+"
            elif salary_min:
                salary_display = f"💰 ₦{salary_min:,}+"
            elif ai_compensation:
                salary_display = f"💰 {ai_compensation}"
            else:
                salary_display = "💰 Competitive salary"

            # Build message
            alert_msg = f"🚨 *JOB MATCH #{index}* ({match_score:.0f}% match)\n\n"
            alert_msg += f"🚀 **{title}** at **{company}**\n"
            alert_msg += f"📍 {location}\n"
            alert_msg += f"{salary_display}\n"

            # Add job URL if available
            if job.get("job_url"):
                alert_msg += f"\n🔗 **Apply:** {job['job_url']}"
            else:
                alert_msg += (
                    f"\n💬 Reply '{index}' for full details and application info"
                )

            return alert_msg

        except Exception as e:
            logger.error(f"❌ Error formatting job with ai_summary: {e}")
            # Simple fallback
            title = job.get("title", "Job Opportunity")
            company = job.get("company", "Company")
            match_score = job.get("match_score", 0)
            return f"🚨 *JOB MATCH #{index}* ({match_score:.0f}% match)\n\n🚀 **{title}** at **{company}**\n💬 Reply '{index}' for details"
