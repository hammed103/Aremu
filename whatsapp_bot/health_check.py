#!/usr/bin/env python3
"""
Health Check Service for AI Enhanced Parser
Provides HTTP endpoints for monitoring the parser service
"""

import os
import sys
from flask import Flask, jsonify
from datetime import datetime

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

@app.route('/health')
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "ai-enhanced-parser",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv('RAILWAY_ENVIRONMENT', 'local')
    })

@app.route('/status')
def status_check():
    """Detailed status check"""
    try:
        # Test database connection
        from data_parser.parsers.ai_enhanced_parser import AIEnhancedJobParser
        parser = AIEnhancedJobParser()
        
        return jsonify({
            "status": "operational",
            "service": "ai-enhanced-parser",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "openai": "configured" if os.getenv('OPENAI_API_KEY') else "missing",
            "whatsapp": "configured" if os.getenv('WHATSAPP_TOKEN') else "missing"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "service": "ai-enhanced-parser", 
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
