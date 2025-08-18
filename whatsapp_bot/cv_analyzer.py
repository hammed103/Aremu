#!/usr/bin/env python3
"""
CV Analyzer for Nigerian Job Market
Provides intelligent CV feedback and improvement suggestions
"""

import openai
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CVAnalyzer:
    """Analyze CVs and provide Nigerian market-specific feedback"""
    
    def __init__(self, openai_client):
        self.client = openai_client
        
    def analyze_cv_text(self, cv_text: str, target_role: str = None) -> Dict:
        """Analyze CV text and provide comprehensive feedback"""
        try:
            # Create analysis prompt
            analysis_prompt = self._create_analysis_prompt(cv_text, target_role)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a Nigerian HR expert and career coach with 10+ years experience in the Nigerian job market. Provide practical, actionable CV feedback."},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse the analysis into structured feedback
            return self._parse_analysis(analysis_text)
            
        except Exception as e:
            logger.error(f"❌ CV analysis error: {e}")
            return {"error": "Unable to analyze CV at the moment"}
    
    def _create_analysis_prompt(self, cv_text: str, target_role: str = None) -> str:
        """Create comprehensive CV analysis prompt"""
        
        role_context = f" for a {target_role} role" if target_role else ""
        
        return f"""
        Analyze this CV{role_context} for the Nigerian job market and provide specific feedback:

        CV CONTENT:
        {cv_text}

        Please provide analysis in this EXACT format:

        **OVERALL SCORE: X/10**

        **STRENGTHS:**
        • [Specific strength 1]
        • [Specific strength 2]
        • [Specific strength 3]

        **AREAS FOR IMPROVEMENT:**
        • [Specific improvement 1]
        • [Specific improvement 2]
        • [Specific improvement 3]

        **NIGERIAN MARKET TIPS:**
        • [Nigeria-specific tip 1]
        • [Nigeria-specific tip 2]
        • [Nigeria-specific tip 3]

        **MISSING SECTIONS:**
        • [What's missing from CV]

        **ATS OPTIMIZATION:**
        • [Keywords to add]
        • [Format improvements]

        **NEXT STEPS:**
        • [Actionable step 1]
        • [Actionable step 2]

        Focus on:
        - Nigerian company expectations
        - Local salary ranges and negotiation
        - Skills in demand in Nigeria
        - Professional formatting standards
        - ATS compatibility for Nigerian companies
        - Industry-specific advice for Nigerian market
        """
    
    def _parse_analysis(self, analysis_text: str) -> Dict:
        """Parse AI analysis into structured format"""
        try:
            sections = {}
            current_section = None
            current_content = []
            
            lines = analysis_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check for section headers
                if line.startswith('**') and line.endswith('**'):
                    # Save previous section
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content)
                    
                    # Start new section
                    current_section = line.replace('**', '').strip()
                    current_content = []
                    
                elif current_section:
                    current_content.append(line)
            
            # Save last section
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content)
            
            return {
                "success": True,
                "analysis": sections,
                "raw_text": analysis_text
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing CV analysis: {e}")
            return {
                "success": False,
                "error": "Failed to parse analysis",
                "raw_text": analysis_text
            }
    
    def get_quick_tips(self, job_type: str = None) -> List[str]:
        """Get quick CV tips for Nigerian job market"""
        
        general_tips = [
            "Include a professional email address (avoid yahoo.com if possible)",
            "Add your location (Lagos, Abuja, etc.) - Nigerian employers prefer local candidates",
            "Use Nigerian English spelling (e.g., 'organisation' not 'organization')",
            "Include relevant certifications and professional courses",
            "Mention any volunteer work or community service",
            "Keep CV to 2 pages maximum for most roles",
            "Include a brief professional summary at the top",
            "Use action verbs: 'Led', 'Managed', 'Implemented', 'Achieved'"
        ]
        
        # Add job-specific tips
        if job_type:
            job_type_lower = job_type.lower()
            
            if "developer" in job_type_lower or "software" in job_type_lower:
                general_tips.extend([
                    "Include GitHub profile and portfolio links",
                    "List specific programming languages and frameworks",
                    "Mention any open-source contributions",
                    "Include relevant bootcamp or online course certificates"
                ])
            elif "sales" in job_type_lower or "business" in job_type_lower:
                general_tips.extend([
                    "Quantify your sales achievements (percentages, targets met)",
                    "Include customer relationship management experience",
                    "Mention any sales training or certifications",
                    "Highlight communication and negotiation skills"
                ])
            elif "marketing" in job_type_lower:
                general_tips.extend([
                    "Include digital marketing certifications (Google, Facebook)",
                    "Mention social media management experience",
                    "Quantify campaign results and ROI",
                    "Include content creation and analytics skills"
                ])
        
        return general_tips[:8]  # Return top 8 tips
    
    def format_analysis_for_whatsapp(self, analysis: Dict) -> str:
        """Format CV analysis for WhatsApp display"""
        
        if not analysis.get("success"):
            return "❌ Unable to analyze your CV. Please try again or send a clearer version."
        
        sections = analysis.get("analysis", {})
        
        # Build WhatsApp-friendly response
        response = "📋 **CV ANALYSIS COMPLETE**\n\n"
        
        # Overall score
        if "OVERALL SCORE" in sections:
            score = sections["OVERALL SCORE"]
            response += f"🎯 **Score:** {score}\n\n"
        
        # Strengths
        if "STRENGTHS" in sections:
            response += "✅ **What's Working Well:**\n"
            response += sections["STRENGTHS"] + "\n\n"
        
        # Improvements
        if "AREAS FOR IMPROVEMENT" in sections:
            response += "🔧 **Areas to Improve:**\n"
            response += sections["AREAS FOR IMPROVEMENT"] + "\n\n"
        
        # Nigerian market tips
        if "NIGERIAN MARKET TIPS" in sections:
            response += "🇳🇬 **Nigerian Market Tips:**\n"
            response += sections["NIGERIAN MARKET TIPS"] + "\n\n"
        
        # Next steps
        if "NEXT STEPS" in sections:
            response += "🎯 **Your Next Steps:**\n"
            response += sections["NEXT STEPS"] + "\n\n"
        
        response += "💡 Need more help? Ask me about interview tips, salary negotiation, or industry insights!"
        
        return response
