"""Pre-process emails using rule-based categorization (no API calls needed)."""

import sys
import json
from database.db_manager import DatabaseManager

def categorize_email_by_rules(email_subject: str, email_body: str, sender: str) -> str:
    """Categorize email using simple rules (no API needed).
    
    Args:
        email_subject: Email subject
        email_body: Email body
        sender: Sender email
        
    Returns:
        Category name
    """
    subject_lower = email_subject.lower()
    body_lower = email_body.lower()
    sender_lower = sender.lower()
    
    # Spam (check first - highest priority)
    if any(word in subject_lower for word in ['urgent verify', 'verify your account', 'suspicious', '90% off', 'flash sale']):
        return 'Spam'
    
    if any(word in sender_lower for word in ['security@banking', 'bank-verify']):
        if 'verify' in subject_lower or 'click' in subject_lower:
            return 'Spam'
    
    # Newsletter (check early)
    if any(word in sender_lower for word in ['newsletter', 'noreply', 'digest']):
        return 'Newsletter'
    
    if any(word in subject_lower for word in ['weekly digest', 'weekly updates', 'top stories', 'top 10', 'newsletter']):
        return 'Newsletter'
    
    # Project Update (specific patterns)
    if 'status update' in subject_lower or 'project status' in subject_lower:
        if any(word in body_lower for word in ['completed:', 'in progress', 'blocked', 'sprint', 'on track']):
            return 'Project Update'
    
    # Important (urgent/critical)
    if any(word in subject_lower for word in ['urgent:', 'critical', 'emergency', 'server downtime', 'bug in production']):
        if 'important' in subject_lower or 'urgent' in subject_lower:
            return 'Important'
    
    # To-Do (action items with deadlines)
    if any(word in subject_lower for word in ['action required', 'approval required', 'code review request', 'review required']):
        return 'To-Do'
    
    if any(word in body_lower for word in ['deadline', 'review by', 'by end of', 'by friday', 'by monday', 'approve by', 'provide feedback by']):
        return 'To-Do'
    
    if 'database migration' in subject_lower or 'expense report approval' in subject_lower:
        return 'To-Do'
    
    # Meeting Request (specific patterns)
    if any(word in subject_lower for word in ['meeting', 'standup', 'conference', 'sprint planning']):
        return 'Meeting Request'
    
    if any(word in body_lower for word in ['join us', 'schedule', 'meeting is scheduled', 'meeting room', 'meeting link']):
        return 'Meeting Request'
    
    # General (default)
    return 'General'

def preprocess_emails():
    """Pre-process all emails with rule-based categorization."""
    print("=" * 70)
    print("Pre-processing Emails with Rule-Based Categorization")
    print("=" * 70)
    
    # Initialize database
    print("\n1. Initializing database...")
    db = DatabaseManager()
    
    # Get all emails
    print("\n2. Loading emails...")
    all_emails = db.get_emails()
    print(f"   Found {len(all_emails)} emails")
    
    if not all_emails:
        print("\n   ⚠️ No emails found. Loading mock inbox...")
        from config import MOCK_INBOX_PATH
        success, message = db.load_mock_inbox(str(MOCK_INBOX_PATH))
        if success:
            print(f"   ✅ {message}")
            all_emails = db.get_emails()
        else:
            print(f"   ❌ Failed to load: {message}")
            return
    
    # Reset all to unprocessed
    print("\n3. Resetting processed flags...")
    reset_count = db.reset_processed_flag()
    print(f"   ✅ Reset {reset_count} emails")
    
    # Clear all action items first
    print("\n4. Clearing old action items...")
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM action_items")
    deleted_actions = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"   ✅ Deleted {deleted_actions} old action items")
    
    # Categorize each email
    print("\n5. Categorizing emails using rules...")
    categorized = {}
    
    for idx, email in enumerate(all_emails):
        subject = email.get('subject', '')
        body = email.get('body', '')
        sender = email.get('sender', '')
        
        # Categorize
        category = categorize_email_by_rules(subject, body, sender)
        
        # Update category
        db.update_email_category(email['id'], category)
        
        # Track counts
        categorized[category] = categorized.get(category, 0) + 1
        
        print(f"   [{idx + 1}/{len(all_emails)}] ✓ {category}: {subject[:50]}")
        
        # Extract action items for To-Do emails
        if category == 'To-Do':
            # Extract deadline if mentioned
            deadline = None
            body_lower = body.lower()
            
            # Look for deadlines
            import re
            deadline_patterns = [
                r'by\s+(?:end\s+of\s+)?(\w+\s+\d{1,2})',  # "by Friday", "by end of week"
                r'deadline[:\s]+(\w+\s+\d{1,2})',  # "deadline: January 19th"
                r'by\s+(\w+\s+\d{1,2})',  # "by January 19th"
            ]
            
            for pattern in deadline_patterns:
                match = re.search(pattern, body_lower)
                if match:
                    deadline = match.group(1)
                    break
            
            # Determine priority
            priority = 'high' if any(word in subject.lower() for word in ['urgent', 'critical', 'immediate']) else 'medium'
            
            # Create action item
            task_text = subject
            if 'review' in body_lower:
                task_text = f"Review: {subject}"
            elif 'approve' in body_lower:
                task_text = f"Approve: {subject}"
            elif 'provide feedback' in body_lower:
                task_text = f"Provide feedback: {subject}"
            
            db.save_action_item(
                email_id=email['id'],
                task=task_text,
                deadline=deadline,
                priority=priority
            )
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ Pre-processing Complete!")
    print("=" * 70)
    print(f"Total emails processed: {len(all_emails)}")
    print("\nCategory Breakdown:")
    for category, count in sorted(categorized.items()):
        print(f"  {category}: {count}")
    
    # Get final stats
    stats = db.get_email_stats()
    print(f"\nPending action items: {stats['pending_actions']}")
    
    print("\n✅ All emails are now categorized!")
    print("   Open the app - categories will be visible immediately.")
    print("=" * 70)

if __name__ == "__main__":
    preprocess_emails()

