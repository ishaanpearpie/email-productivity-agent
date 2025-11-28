"""Email processor agent for categorization and action extraction."""

import logging
from typing import List, Dict, Any, Optional

from database.db_manager import DatabaseManager
from prompts.prompt_manager import PromptManager
from utils.gemini_client import GeminiClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailProcessor:
    """Processes emails using LLM for categorization and action extraction."""
    
    def __init__(self, db_manager: DatabaseManager, 
                 prompt_manager: PromptManager,
                 gemini_client: GeminiClient):
        """Initialize email processor.
        
        Args:
            db_manager: Database manager instance
            prompt_manager: Prompt manager instance
            gemini_client: Gemini API client instance
        """
        self.db = db_manager
        self.prompt_manager = prompt_manager
        self.gemini = gemini_client
    
    def categorize_email(self, email_content: Dict[str, Any], 
                        prompt: Optional[str] = None) -> str:
        """Categorize email using LLM.
        
        Args:
            email_content: Email dictionary with sender, subject, body
            prompt: Optional custom prompt
            
        Returns:
            Category name or 'Uncategorized' if failed
        """
        try:
            # Get prompt
            if not prompt:
                prompt = self.prompt_manager.get_prompt('categorization')
            
            if not prompt:
                logger.error("No categorization prompt found")
                return 'Uncategorized'
            
            # Build full prompt - use shorter format for faster processing
            email_text = f"From: {email_content.get('sender', '')}\n"
            email_text += f"Subject: {email_content.get('subject', '')}\n"
            email_text += f"Body: {email_content.get('body', '')[:500]}\n"  # Limit body length
            
            full_prompt = f"{prompt}\n\nEmail:\n{email_text}"
            
            # Call Gemini API - use shorter timeout
            result = self.gemini.generate_completion(full_prompt, max_tokens=50)
            
            # If it fails, return Uncategorized quickly
            if not result['success']:
                error_msg = result.get('error', 'Unknown')[:50] if result.get('error') else 'Unknown'
                logger.warning(f"Categorization failed for email {email_content.get('id')}: {error_msg}")
                return 'Uncategorized'
            
            if result.get('response'):
                category = result['response'].strip()
                # Clean up category name - remove common prefixes/suffixes
                category = category.replace('Category:', '').replace('category:', '').strip()
                category = category.split('\n')[0].split('.')[0].strip()  # Take first line, remove periods
                category = category.strip('"').strip("'").strip()  # Remove quotes
                
                logger.info(f"Categorized email {email_content.get('id')} as: {category}")
                
                # Validate category
                valid_categories = [
                    'Important', 'Newsletter', 'Spam', 'To-Do', 
                    'Project Update', 'Meeting Request', 'General'
                ]
                
                # Check if category matches (case-insensitive)
                category_lower = category.lower()
                for valid_cat in valid_categories:
                    if valid_cat.lower() == category_lower or valid_cat.lower() in category_lower:
                        logger.info(f"Matched category: {valid_cat}")
                        return valid_cat
                
                # Try fuzzy matching for common variations
                category_map = {
                    'important': 'Important',
                    'newsletter': 'Newsletter',
                    'spam': 'Spam',
                    'todo': 'To-Do',
                    'to-do': 'To-Do',
                    'to do': 'To-Do',
                    'project update': 'Project Update',
                    'meeting request': 'Meeting Request',
                    'meeting': 'Meeting Request',
                    'general': 'General'
                }
                
                for key, value in category_map.items():
                    if key in category_lower:
                        logger.info(f"Fuzzy matched category: {value}")
                        return value
                
                # If not found, return as-is if it looks reasonable
                if len(category) < 50 and category != '':
                    logger.warning(f"Using unrecognized category: {category}")
                    return category
                
                logger.warning(f"Could not determine category, using 'Uncategorized'")
                return 'Uncategorized'
            else:
                logger.error(f"Failed to categorize email: {result.get('error')}")
                self.db.log_processing(
                    email_id=email_content.get('id'),
                    operation_type='categorization',
                    status='failed',
                    error_message=result.get('error')
                )
                return 'Uncategorized'
        
        except Exception as e:
            logger.error(f"Error categorizing email: {e}")
            self.db.log_processing(
                email_id=email_content.get('id'),
                operation_type='categorization',
                status='failed',
                error_message=str(e)
            )
            return 'Uncategorized'
    
    def extract_action_items(self, email_content: Dict[str, Any],
                            prompt: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract action items from email.
        
        Args:
            email_content: Email dictionary
            prompt: Optional custom prompt
            
        Returns:
            List of action item dictionaries
        """
        try:
            # Get prompt
            if not prompt:
                prompt = self.prompt_manager.get_prompt('action_extraction')
            
            if not prompt:
                logger.error("No action extraction prompt found")
                return []
            
            # Build full prompt
            email_text = f"Sender: {email_content.get('sender', '')}\n"
            email_text += f"Subject: {email_content.get('subject', '')}\n"
            email_text += f"Body: {email_content.get('body', '')}\n"
            
            full_prompt = f"{prompt}\n\nEmail:\n{email_text}"
            
            # Call Gemini API
            result = self.gemini.generate_completion(full_prompt, max_tokens=500)
            
            if result['success'] and result['response']:
                # Parse JSON response
                parsed = self.gemini.parse_json_response(result['response'])
                
                tasks = parsed.get('tasks', [])
                
                # Validate and clean tasks
                action_items = []
                for task in tasks:
                    if isinstance(task, dict) and 'task' in task:
                        action_items.append({
                            'task': task.get('task', '').strip(),
                            'deadline': task.get('deadline', '').strip() if task.get('deadline') else None,
                            'priority': task.get('priority', 'medium').lower()
                        })
                
                # Log success
                self.db.log_processing(
                    email_id=email_content.get('id'),
                    operation_type='action_extraction',
                    status='success',
                    error_message=None
                )
                
                return action_items
            else:
                logger.error(f"Failed to extract action items: {result.get('error')}")
                self.db.log_processing(
                    email_id=email_content.get('id'),
                    operation_type='action_extraction',
                    status='failed',
                    error_message=result.get('error')
                )
                return []
        
        except Exception as e:
            logger.error(f"Error extracting action items: {e}")
            self.db.log_processing(
                email_id=email_content.get('id'),
                operation_type='action_extraction',
                status='failed',
                error_message=str(e)
            )
            return []
    
    def process_email(self, email_id: int) -> Dict[str, Any]:
        """Process a single email (categorize + extract actions).
        
        Args:
            email_id: Email ID
            
        Returns:
            Dictionary with processing results
        """
        email = self.db.get_email_by_id(email_id)
        if not email:
            return {'success': False, 'error': 'Email not found'}
        
        # Categorize
        category = self.categorize_email(email)
        self.db.update_email_category(email_id, category)
        
        # Extract action items
        action_items = self.extract_action_items(email)
        
        # Save action items
        saved_items = []
        for item in action_items:
            item_id = self.db.save_action_item(
                email_id=email_id,
                task=item['task'],
                deadline=item.get('deadline'),
                priority=item.get('priority', 'medium')
            )
            if item_id:
                saved_items.append(item_id)
        
        return {
            'success': True,
            'category': category,
            'action_items_count': len(saved_items)
        }
    
    def process_inbox(self, limit: Optional[int] = None, 
                     progress_callback: Optional[callable] = None,
                     skip_action_extraction: bool = False) -> Dict[str, Any]:
        """Process all unprocessed emails.
        
        Args:
            limit: Optional limit on number of emails to process
            progress_callback: Optional callback function(processed, total, current_email_subject)
            skip_action_extraction: If True, only categorize (faster)
            
        Returns:
            Dictionary with processing statistics
        """
        unprocessed = self.db.get_emails(is_processed=False, limit=limit)
        
        if not unprocessed:
            return {
                'success': True,
                'processed': 0,
                'failed': 0,
                'message': 'No unprocessed emails found'
            }
        
        total = len(unprocessed)
        processed_count = 0
        failed_count = 0
        errors = []
        
        for idx, email in enumerate(unprocessed):
            try:
                # Update progress
                if progress_callback:
                    progress_callback(idx + 1, total, email.get('subject', 'Unknown'))
                
                # Small delay to avoid rate limiting (except for first email)
                if idx > 0:
                    import time
                    time.sleep(0.2)  # Reduced to 200ms for faster processing
                
                # Process email (categorize only if skip_action_extraction)
                if skip_action_extraction:
                    # Just categorize - mark as processed even if it fails
                    category = self.categorize_email(email)
                    self.db.update_email_category(email['id'], category)  # Will save even if Uncategorized
                    if category and category != 'Uncategorized':
                        processed_count += 1
                        logger.info(f"✓ Email {email['id']} - Category: {category}")
                    else:
                        failed_count += 1
                        errors.append(f"Email {email['id']}: Categorized as {category}")
                else:
                    # Full processing
                    result = self.process_email(email['id'])
                    if result['success']:
                        processed_count += 1
                        logger.info(f"✓ Email {email['id']} - Category: {result.get('category')}")
                    else:
                        failed_count += 1
                        error_msg = result.get('error', 'Unknown error')
                        errors.append(f"Email {email['id']}: {error_msg}")
                
            except Exception as e:
                logger.error(f"Error processing email {email['id']}: {e}")
                failed_count += 1
                errors.append(f"Email {email['id']}: {str(e)[:100]}")
                # Continue processing next email - don't stop on errors
                continue
        
        result = {
            'success': True,
            'processed': processed_count,
            'failed': failed_count,
            'total': total
        }
        
        if errors:
            result['errors'] = errors[:5]  # Include first 5 errors
        
        return result


