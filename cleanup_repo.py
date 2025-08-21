#!/usr/bin/env python3
"""
Repository cleanup script to remove unnecessary files and organize the codebase
"""

import os
import shutil
import glob

def cleanup_repository():
    """Clean up unnecessary files from the repository"""
    
    print("🧹 Starting Repository Cleanup")
    print("=" * 50)
    
    # Files and directories to remove
    cleanup_items = [
        # Test files in whatsapp_bot
        "whatsapp_bot/test_*.py",
        "whatsapp_bot/fix_*.py",
        "whatsapp_bot/send_test_message.py",
        "whatsapp_bot/debug_reminder_system.py",
        
        # Log files
        "whatsapp_bot/whatsapp_bot.log",
        "data_parser/ai_enhanced_parser.log",
        "job_data_parser.log",
        "scraper/fixed_jobspy.log",
        
        # HTML ad templates (unused)
        "instagram-square-ad.html",
        "instagram-story-ad.html",
        "mobile-ad-template.html",
        "whatsapp-focused-ad.html",
        
        # Duplicate frontend
        "FE",  # We have whatsapp_bot/frontend
        
        # Archive directories
        "data_parser/archive",
        
        # Python cache directories
        "**/__pycache__",
        "whatsapp_bot/__pycache__",
        "data_parser/__pycache__",
        
        # Temporary fix scripts in root
        "fix_existing_ai_summaries.py",
        "reorganize_canonical_jobs.py",
        "test_nysc_detection.py",
        
        # Unused documentation files
        "whatsapp_bot/24H_REMINDER_SYSTEM.md",
        "whatsapp_bot/CLEANUP_SUMMARY.md",
        "whatsapp_bot/PRODUCTION_SUMMARY.md",
        "whatsapp_bot/RAILWAY_DEPLOYMENT.md",
        "whatsapp_bot/UNIFIED_DEPLOYMENT.md",
        "whatsapp_bot/deploy.md",
        "whatsapp_bot/user_scenarios.md",
        
        # Duplicate config files
        "whatsapp_bot/setup.py",  # We have requirements.txt
        
        # Service files (if not needed)
        "whatsapp_bot/aremu-reminder.service",
        
        # Unused utilities
        "database/add_missing_column.py",
        "database/final_schema_fix.py", 
        "database/fix_schema.py",
        "database/check_data.py",
        "database/import_all.py",
        
        # Legacy/unused files
        "whatsapp_bot/cv_analyzer.py",  # If not used
        "whatsapp_bot/nigerian_career_advisor.py",  # If not used
    ]
    
    removed_count = 0
    
    for item in cleanup_items:
        # Handle glob patterns
        if "*" in item:
            matches = glob.glob(item, recursive=True)
            for match in matches:
                if os.path.exists(match):
                    try:
                        if os.path.isdir(match):
                            shutil.rmtree(match)
                            print(f"🗑️  Removed directory: {match}")
                        else:
                            os.remove(match)
                            print(f"🗑️  Removed file: {match}")
                        removed_count += 1
                    except Exception as e:
                        print(f"❌ Failed to remove {match}: {e}")
        else:
            if os.path.exists(item):
                try:
                    if os.path.isdir(item):
                        shutil.rmtree(item)
                        print(f"🗑️  Removed directory: {item}")
                    else:
                        os.remove(item)
                        print(f"🗑️  Removed file: {item}")
                    removed_count += 1
                except Exception as e:
                    print(f"❌ Failed to remove {item}: {e}")
    
    print(f"\n✅ Cleanup complete! Removed {removed_count} items")
    
    # Create a clean directory structure summary
    print("\n📁 Cleaned Repository Structure:")
    print("├── README.md")
    print("├── data_parser/")
    print("│   ├── parsers/")
    print("│   ├── smart_delivery_engine.py")
    print("│   └── utils/")
    print("├── database/")
    print("│   ├── config.py")
    print("│   ├── raw_jobs_schema.sql")
    print("│   └── requirements.txt")
    print("├── scraper/")
    print("│   ├── indeed/")
    print("│   ├── jobspy/")
    print("│   ├── linkedin/")
    print("│   ├── prosple/")
    print("│   └── requirements.txt")
    print("├── whatsapp_bot/")
    print("│   ├── agents/")
    print("│   ├── app.py")
    print("│   ├── core/")
    print("│   ├── database_manager.py")
    print("│   ├── frontend/")
    print("│   ├── legacy/")
    print("│   ├── reminder_daemon.py")
    print("│   ├── requirements.txt")
    print("│   ├── services/")
    print("│   ├── utils/")
    print("│   └── webhooks/")
    print("├── jobs.csv")
    print("├── package.json")
    print("├── railway.json")
    print("├── start.js")
    print("└── venv/")
    
    print("\n🎯 Key Benefits:")
    print("✅ Removed test and debug files")
    print("✅ Cleaned up log files")
    print("✅ Removed duplicate documentation")
    print("✅ Eliminated unused HTML templates")
    print("✅ Removed Python cache directories")
    print("✅ Streamlined directory structure")
    
    print("\n💡 Remaining Core Components:")
    print("🤖 WhatsApp Bot - Main application")
    print("📊 Data Parser - Job processing and AI enhancement")
    print("🗄️  Database - Schema and configuration")
    print("🔍 Scraper - Job data collection")
    print("🌐 Frontend - User interface")

if __name__ == "__main__":
    cleanup_repository()
