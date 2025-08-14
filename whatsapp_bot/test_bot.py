#!/usr/bin/env python3
"""
Test script for Aremu WhatsApp Bot
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get("http://localhost:5000/")
        print("🏥 Health Check:")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    except Exception as e:
        print(f"❌ Health check failed: {e}")

def test_webhook_verification():
    """Test webhook verification"""
    try:
        verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "aremu_verify_token")
        url = f"http://localhost:5000/webhook?hub.mode=subscribe&hub.verify_token={verify_token}&hub.challenge=test_challenge"
        
        response = requests.get(url)
        print("🔐 Webhook Verification:")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        print()
    except Exception as e:
        print(f"❌ Webhook verification failed: {e}")

def test_send_message():
    """Test manual message sending"""
    try:
        # Note: This will only work if you have valid WhatsApp credentials
        test_data = {
            "phone_number": "2348123456789",  # Replace with a test number
            "message": "Hello! This is a test message from Aremu bot."
        }
        
        response = requests.post(
            "http://localhost:5000/send",
            headers={"Content-Type": "application/json"},
            json=test_data
        )
        
        print("📱 Send Message Test:")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    except Exception as e:
        print(f"❌ Send message test failed: {e}")

def test_webhook_message():
    """Test incoming webhook message processing"""
    try:
        # Simulate a WhatsApp webhook message
        webhook_data = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "2348123456789",
                            "type": "text",
                            "text": {
                                "body": "Hello, I'm looking for software engineering jobs in Lagos"
                            }
                        }]
                    }
                }]
            }]
        }
        
        response = requests.post(
            "http://localhost:5000/webhook",
            headers={"Content-Type": "application/json"},
            json=webhook_data
        )
        
        print("📥 Webhook Message Test:")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
    except Exception as e:
        print(f"❌ Webhook message test failed: {e}")

def main():
    """Run all tests"""
    print("🧪 Testing Aremu WhatsApp Bot")
    print("=" * 40)
    
    print("Make sure the Flask app is running on localhost:5000")
    print("Run: python app.py")
    print()
    
    # Run tests
    test_health_check()
    test_webhook_verification()
    
    # Only test these if you have valid credentials
    if os.getenv("WHATSAPP_ACCESS_TOKEN"):
        test_send_message()
        test_webhook_message()
    else:
        print("⚠️  WhatsApp credentials not found - skipping WhatsApp API tests")
        print("   Add WHATSAPP_ACCESS_TOKEN to .env file to test WhatsApp functionality")

if __name__ == "__main__":
    main()
