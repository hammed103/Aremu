#!/usr/bin/env python3
"""
Apply Button Designer - Creates better apply button designs for job listings
"""

import logging
from typing import Dict, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ApplyButtonDesigner:
    """Designs better apply buttons based on job source and context"""

    def __init__(self):
        """Initialize the apply button designer"""
        self.company_specific_buttons = {
            # Tech companies
            "google": "🚀 Apply at Google",
            "microsoft": "💼 Apply at Microsoft",
            "apple": "🍎 Apply at Apple",
            "meta": "📘 Apply at Meta",
            "amazon": "📦 Apply at Amazon",
            "netflix": "🎬 Apply at Netflix",
            # Job boards
            "linkedin": "💼 Apply on LinkedIn",
            "indeed": "🔍 Apply on Indeed",
            "glassdoor": "🏢 Apply on Glassdoor",
            "jobvacancy": "💼 Apply on JobVacancy",
            "jobberman": "🇳🇬 Apply Jobberman",
            "myjobmag": "📋 Apply on MyJobMag",
            # Nigerian companies
            "gtbank": "🏦 Apply at GTBank",
            "dangote": "🏭 Apply at Dangote",
            "mtn": "📱 Apply at MTN",
            "access": "🏦 Apply at Access Bank",
            "zenith": "🏦 Apply at Zenith Bank",
        }

        self.role_specific_buttons = {
            "software": "💻 Apply as Developer",
            "engineer": "⚙️ Apply as Engineer",
            "manager": "👔 Apply as Manager",
            "analyst": "📊 Apply as Analyst",
            "designer": "🎨 Apply as Designer",
            "marketing": "📢 Apply for Marketing",
            "sales": "💰 Apply for Sales",
            "finance": "💳 Apply for Finance",
            "hr": "👥 Apply for HR Role",
            "data": "📈 Apply for Data Role",
        }

    def get_apply_button_text(
        self,
        job_url: str,
        company: str = None,
        job_title: str = None,
        job_source: str = None,
    ) -> str:
        """Get the best apply button text based on context"""
        try:
            # Extract domain from URL for smart detection
            if job_url:
                domain = urlparse(job_url).netloc.lower()

                # Check for specific company domains
                for company_key, button_text in self.company_specific_buttons.items():
                    if company_key in domain:
                        return button_text

                # Check for job board domains
                if "linkedin.com" in domain:
                    return "💼 Apply on LinkedIn"
                elif "indeed.com" in domain:
                    return "🔍 Apply on Indeed"
                elif "glassdoor.com" in domain:
                    return "🏢 Apply on Glassdoor"
                elif "jobberman.com" in domain:
                    return "🇳🇬 Apply on Jobberman"
                elif "myjobmag.com" in domain:
                    return "📋 Apply on MyJobMag"

            # Check company name
            if company:
                company_lower = company.lower()
                for company_key, button_text in self.company_specific_buttons.items():
                    if company_key in company_lower:
                        return button_text

            # Check job title for role-specific buttons
            if job_title:
                title_lower = job_title.lower()
                for role_key, button_text in self.role_specific_buttons.items():
                    if role_key in title_lower:
                        return button_text

            # Default professional button
            return "🚀 Apply for this Job"

        except Exception as e:
            logger.error(f"Error generating apply button text: {e}")
            return "🚀 Apply for this Job"

    def get_fallback_apply_section(
        self, job_url: str, company: str = None, job_title: str = None
    ) -> str:
        """Get a well-formatted fallback apply section when CTA button fails"""
        try:
            button_text = self.get_apply_button_text(job_url, company, job_title)

            # Remove emoji from button text for fallback
            clean_text = (
                button_text.replace("🚀", "")
                .replace("💼", "")
                .replace("🔍", "")
                .replace("🏢", "")
                .replace("🇳🇬", "")
                .replace("📋", "")
                .strip()
            )

            fallback = (
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎯 **{clean_text.upper()}**\n"
                f"👆 Click the link below to apply:\n"
                f"🔗 {job_url}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )

            return fallback

        except Exception as e:
            logger.error(f"Error generating fallback apply section: {e}")
            return f"🔗 Apply: {job_url}"

    def get_apply_instructions(self, job_source: str = None) -> str:
        """Get contextual apply instructions"""
        instructions = {
            "linkedin": "💡 Tip: Make sure your LinkedIn profile is updated before applying!",
            "indeed": "💡 Tip: Upload your latest CV for faster applications!",
            "jobberman": "💡 Tip: Complete your Jobberman profile for better matches!",
            "company": "💡 Tip: Research the company before applying!",
        }

        return instructions.get(
            job_source, "💡 Tip: Tailor your application to this specific role!"
        )


# Global instance for easy access
apply_button_designer = ApplyButtonDesigner()
