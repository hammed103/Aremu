#!/usr/bin/env python3
"""
Extract URLs from existing WhatsApp jobs and update their job_url field
"""

import sys
import os
import re
sys.path.append(os.path.join(os.path.dirname(__file__), 'whatsapp_bot'))

from database_manager import DatabaseManager

def extract_url_from_text(text: str) -> str:
    """Extract URLs from WhatsApp job text for CTA buttons"""
    if not text:
        return None
    
    # URL patterns to match various formats
    url_patterns = [
        # Standard HTTP/HTTPS URLs
        r'https?://[^\s<>"{}|\\^`\[\]]+',
        # URLs without protocol
        r'www\.[^\s<>"{}|\\^`\[\]]+',
        # Common job board domains without www
        r'\b(?:linkedin\.com|indeed\.com|glassdoor\.com|jobberman\.com|myjobmag\.com|careers\.[\w-]+\.com)[^\s<>"{}|\\^`\[\]]*',
        # Application links
        r'\b[\w-]+\.com/(?:jobs|careers|apply)[^\s<>"{}|\\^`\[\]]*',
    ]
    
    for pattern in url_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            url = matches[0]
            # Clean up the URL
            url = url.rstrip('.,!?;)')  # Remove trailing punctuation
            
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Validate URL format
            if is_valid_url(url):
                return url
    
    return None

def is_valid_url(url: str) -> bool:
    """Validate if extracted URL is properly formatted"""
    # Basic URL validation
    url_regex = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_regex.match(url) is not None

def update_whatsapp_jobs_with_urls():
    """Update existing WhatsApp jobs to extract URLs from descriptions"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        print("=== EXTRACTING URLs FROM WHATSAPP JOBS ===\n")
        
        # Find WhatsApp jobs without job_url but with descriptions
        cursor.execute("""
            SELECT id, title, description
            FROM canonical_jobs 
            WHERE source = 'whatsapp' 
              AND (job_url IS NULL OR job_url = '')
              AND description IS NOT NULL 
              AND description != ''
            ORDER BY created_at DESC
        """)
        
        jobs = cursor.fetchall()
        print(f"📊 Found {len(jobs)} WhatsApp jobs without URLs")
        
        updated_count = 0
        urls_found = 0
        
        for job in jobs:
            job_id, title, description = job
            
            # Extract URL from description
            extracted_url = extract_url_from_text(description)
            
            if extracted_url:
                urls_found += 1
                print(f"\n✅ Found URL in: {title}")
                print(f"   🔗 URL: {extracted_url}")
                
                # Update the job with extracted URL
                cursor.execute("""
                    UPDATE canonical_jobs 
                    SET job_url = %s, updated_at = NOW()
                    WHERE id = %s
                """, (extracted_url, job_id))
                
                updated_count += 1
                print(f"   ✅ Updated job ID {job_id}")
            else:
                print(f"❌ No URL found in: {title}")
        
        # Commit changes
        conn.commit()
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total WhatsApp jobs checked: {len(jobs)}")
        print(f"   URLs found: {urls_found}")
        print(f"   Jobs updated: {updated_count}")
        print(f"   Success rate: {(urls_found/len(jobs)*100):.1f}%" if jobs else "0%")
        
        if updated_count > 0:
            print(f"\n🎉 Successfully updated {updated_count} WhatsApp jobs with URLs!")
            print("These jobs will now show CTA buttons when sent to users.")
        else:
            print("\n⚠️  No URLs were found in WhatsApp job descriptions.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_whatsapp_jobs_with_urls()
