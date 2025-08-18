#!/usr/bin/env python3
"""
Nigerian Career Advisor
Provides career advice, market insights, and tips specific to Nigeria
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class NigerianCareerAdvisor:
    """Provides Nigerian job market specific career advice"""
    
    def __init__(self):
        self.current_year = datetime.now().year
        
    def get_salary_insights(self, job_type: str, location: str = "Lagos") -> Dict:
        """Get salary insights for Nigerian job market"""
        
        # Nigerian salary ranges (in Naira per month)
        salary_data = {
            "software developer": {
                "entry": {"min": 150000, "max": 300000},
                "mid": {"min": 300000, "max": 600000},
                "senior": {"min": 600000, "max": 1200000},
                "skills_premium": ["React", "Python", "AWS", "DevOps", "Machine Learning"]
            },
            "frontend developer": {
                "entry": {"min": 120000, "max": 250000},
                "mid": {"min": 250000, "max": 500000},
                "senior": {"min": 500000, "max": 1000000},
                "skills_premium": ["React", "Vue.js", "TypeScript", "Next.js"]
            },
            "product manager": {
                "entry": {"min": 200000, "max": 400000},
                "mid": {"min": 400000, "max": 800000},
                "senior": {"min": 800000, "max": 1500000},
                "skills_premium": ["Agile", "Data Analysis", "User Research", "SQL"]
            },
            "sales representative": {
                "entry": {"min": 80000, "max": 150000},
                "mid": {"min": 150000, "max": 300000},
                "senior": {"min": 300000, "max": 600000},
                "skills_premium": ["CRM", "Digital Marketing", "B2B Sales"]
            },
            "marketing manager": {
                "entry": {"min": 120000, "max": 250000},
                "mid": {"min": 250000, "max": 500000},
                "senior": {"min": 500000, "max": 1000000},
                "skills_premium": ["Digital Marketing", "SEO", "Google Ads", "Analytics"]
            },
            "data analyst": {
                "entry": {"min": 150000, "max": 300000},
                "mid": {"min": 300000, "max": 600000},
                "senior": {"min": 600000, "max": 1200000},
                "skills_premium": ["Python", "SQL", "Tableau", "Power BI", "Machine Learning"]
            }
        }
        
        job_key = job_type.lower()
        for key in salary_data:
            if key in job_key or job_key in key:
                data = salary_data[key]
                
                # Adjust for location
                location_multiplier = self._get_location_multiplier(location)
                
                return {
                    "job_type": job_type,
                    "location": location,
                    "entry_level": {
                        "min": int(data["entry"]["min"] * location_multiplier),
                        "max": int(data["entry"]["max"] * location_multiplier)
                    },
                    "mid_level": {
                        "min": int(data["mid"]["min"] * location_multiplier),
                        "max": int(data["mid"]["max"] * location_multiplier)
                    },
                    "senior_level": {
                        "min": int(data["senior"]["min"] * location_multiplier),
                        "max": int(data["senior"]["max"] * location_multiplier)
                    },
                    "premium_skills": data["skills_premium"],
                    "currency": "NGN",
                    "period": "monthly"
                }
        
        # Default response for unknown job types
        return {
            "job_type": job_type,
            "location": location,
            "message": "Salary data not available for this role. Consider researching on Glassdoor Nigeria or PayScale.",
            "general_advice": "Nigerian salaries vary widely. Focus on building in-demand skills and negotiating based on value delivered."
        }
    
    def _get_location_multiplier(self, location: str) -> float:
        """Get salary multiplier based on Nigerian location"""
        location_lower = location.lower()
        
        if "lagos" in location_lower:
            return 1.0  # Base rate
        elif "abuja" in location_lower:
            return 0.9
        elif "port harcourt" in location_lower:
            return 0.8
        elif "kano" in location_lower or "kaduna" in location_lower:
            return 0.7
        elif "ibadan" in location_lower or "benin" in location_lower:
            return 0.75
        else:
            return 0.7  # Other locations
    
    def get_interview_tips(self, job_type: str = None) -> List[str]:
        """Get interview tips for Nigerian job market"""
        
        general_tips = [
            "Arrive 15-30 minutes early - Lagos traffic is unpredictable",
            "Dress formally - Nigerian companies value professional appearance",
            "Bring printed copies of your CV and certificates",
            "Research the company's Nigerian operations and local impact",
            "Prepare to discuss how you'll add value to their Nigerian team",
            "Be ready to negotiate salary in Naira, not dollars",
            "Show enthusiasm for working in Nigeria long-term",
            "Mention any local connections or understanding of Nigerian culture"
        ]
        
        if job_type:
            job_type_lower = job_type.lower()
            
            if "developer" in job_type_lower or "software" in job_type_lower:
                general_tips.extend([
                    "Be prepared for technical coding challenges",
                    "Discuss experience with Nigerian fintech or e-commerce",
                    "Mention any remote work experience (popular in Nigerian tech)",
                    "Show knowledge of local tech ecosystem (Paystack, Flutterwave, etc.)"
                ])
            elif "sales" in job_type_lower:
                general_tips.extend([
                    "Discuss understanding of Nigerian consumer behavior",
                    "Mention experience with local payment methods (bank transfers, USSD)",
                    "Show knowledge of different Nigerian markets and regions",
                    "Demonstrate relationship-building skills"
                ])
        
        return general_tips[:10]
    
    def get_industry_insights(self, industry: str = None) -> Dict:
        """Get insights about Nigerian job market trends"""
        
        insights = {
            "tech": {
                "growth": "🚀 Rapidly growing",
                "trends": [
                    "Fintech dominance (Paystack, Flutterwave, Kuda)",
                    "E-commerce expansion (Jumia, Konga)",
                    "Remote work becoming standard",
                    "Blockchain and crypto adoption",
                    "AI/ML roles increasing"
                ],
                "top_companies": ["Paystack", "Flutterwave", "Andela", "Interswitch", "SystemSpecs"],
                "skills_in_demand": ["React", "Python", "Node.js", "AWS", "DevOps"]
            },
            "banking": {
                "growth": "📈 Stable with digital transformation",
                "trends": [
                    "Digital banking revolution",
                    "Mobile money integration",
                    "Regulatory compliance focus",
                    "Customer experience improvement",
                    "Cybersecurity emphasis"
                ],
                "top_companies": ["GTBank", "Access Bank", "Zenith Bank", "First Bank", "UBA"],
                "skills_in_demand": ["Digital Banking", "Risk Management", "Compliance", "Data Analysis"]
            },
            "oil_gas": {
                "growth": "⚡ Transitioning",
                "trends": [
                    "Renewable energy adoption",
                    "Local content development",
                    "Digital transformation",
                    "Environmental compliance",
                    "Skills diversification"
                ],
                "top_companies": ["Shell", "Chevron", "Total", "NNPC", "Seplat"],
                "skills_in_demand": ["Project Management", "HSE", "Engineering", "Data Analysis"]
            }
        }
        
        if industry and industry.lower() in insights:
            return insights[industry.lower()]
        
        return {
            "general": "Nigerian job market is evolving rapidly with tech leading growth",
            "advice": "Focus on digital skills, continuous learning, and building professional networks"
        }
    
    def get_networking_tips(self) -> List[str]:
        """Get networking tips for Nigerian professionals"""
        
        return [
            "Join Nigerian professional associations in your field",
            "Attend Lagos Business School events and seminars",
            "Participate in tech meetups (Lagos, Abuja tech communities)",
            "Use LinkedIn actively - many Nigerian recruiters are active there",
            "Attend industry conferences (Nigeria FinTech Week, etc.)",
            "Join WhatsApp professional groups in your industry",
            "Volunteer for reputable NGOs to build connections",
            "Attend university alumni events",
            "Join co-working spaces in Lagos (CcHub, Zone Tech Park)",
            "Participate in online Nigerian professional forums"
        ]
    
    def format_salary_info_for_whatsapp(self, salary_info: Dict) -> str:
        """Format salary information for WhatsApp"""
        
        if "message" in salary_info:
            return f"💰 **Salary Info: {salary_info['job_type']}**\n\n{salary_info['message']}\n\n💡 {salary_info['general_advice']}"
        
        response = f"💰 **Salary Ranges: {salary_info['job_type']} in {salary_info['location']}**\n\n"
        
        response += f"🟢 **Entry Level:** ₦{salary_info['entry_level']['min']:,} - ₦{salary_info['entry_level']['max']:,}/month\n\n"
        response += f"🟡 **Mid Level:** ₦{salary_info['mid_level']['min']:,} - ₦{salary_info['mid_level']['max']:,}/month\n\n"
        response += f"🔴 **Senior Level:** ₦{salary_info['senior_level']['min']:,} - ₦{salary_info['senior_level']['max']:,}/month\n\n"
        
        if salary_info.get('premium_skills'):
            response += f"⭐ **Premium Skills:** {', '.join(salary_info['premium_skills'])}\n\n"
        
        response += "💡 *Salaries vary by company size, experience, and negotiation skills*"
        
        return response
