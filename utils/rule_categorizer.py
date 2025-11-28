"""Rule-based email categorization (no API calls needed)."""

import re
from typing import Dict, Any


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


def auto_categorize_emails(db_manager, emails: list) -> int:
    """Automatically categorize a list of emails using rules.
    
    Args:
        db_manager: DatabaseManager instance
        emails: List of email dictionaries
        
    Returns:
        Number of emails categorized
    """
    categorized_count = 0
    
    for email in emails:
        # Skip if already categorized
        if email.get('category') and email.get('category') != 'Uncategorized':
            continue
        
        subject = email.get('subject', '')
        body = email.get('body', '')
        sender = email.get('sender', '')
        
        # Categorize using rules
        category = categorize_email_by_rules(subject, body, sender)
        
        # Update category in database
        db_manager.update_email_category(email['id'], category)
        categorized_count += 1
        
        # Extract action items for To-Do emails
        if category == 'To-Do':
            body_lower = body.lower()
            deadline = None
            
            # Look for deadlines
            deadline_patterns = [
                r'by\s+(?:end\s+of\s+)?(\w+\s+\d{1,2})',
                r'deadline[:\s]+(\w+\s+\d{1,2})',
                r'by\s+(\w+\s+\d{1,2})',
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
            
            db_manager.save_action_item(
                email_id=email['id'],
                task=task_text,
                deadline=deadline,
                priority=priority
            )
    
    return categorized_count

