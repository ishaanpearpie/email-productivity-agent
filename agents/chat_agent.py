"""Chat agent for email inbox queries."""

import logging
from typing import List, Dict, Any, Optional

from database.db_manager import DatabaseManager
from utils.gemini_client import GeminiClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailChatAgent:
    """Chat agent for answering inbox-related questions."""
    
    def __init__(self, db_manager: DatabaseManager, gemini_client: GeminiClient):
        """Initialize chat agent.
        
        Args:
            db_manager: Database manager instance
            gemini_client: Gemini API client instance
        """
        self.db = db_manager
        self.gemini = gemini_client
        self.conversation_history: List[Dict[str, str]] = []
    
    def _build_context(self) -> str:
        """Build context from database for RAG-like retrieval.
        
        Returns:
            Context string
        """
        stats = self.db.get_email_stats()
        emails = self.db.get_emails(limit=10)
        
        context = f"Email Inbox Statistics:\n"
        context += f"- Total emails: {stats['total_emails']}\n"
        context += f"- Categories: {stats['category_counts']}\n"
        context += f"- Pending action items: {stats['pending_actions']}\n\n"
        
        context += "Recent Emails:\n"
        for email in emails[:5]:
            context += f"- [{email['category']}] {email['subject']} (from {email['sender']})\n"
        
        return context
    
    def answer_query(self, user_query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Answer user query about inbox.
        
        Args:
            user_query: User's question
            context: Optional additional context
            
        Returns:
            Dictionary with answer and metadata
        """
        try:
            # Build system context
            inbox_context = self._build_context()
            if context:
                inbox_context += f"\nAdditional Context:\n{context}\n"
            
            # Build conversation history
            history_text = ""
            if self.conversation_history:
                history_text = "\nPrevious conversation:\n"
                for msg in self.conversation_history[-5:]:  # Last 5 messages
                    history_text += f"{msg['role']}: {msg['content']}\n"
            
            # Build full prompt
            system_instruction = """You are an intelligent email assistant. Answer questions about the user's email inbox based on the provided context. Be concise and helpful."""
            
            prompt = f"{system_instruction}\n\n{inbox_context}\n{history_text}\n\nUser: {user_query}\n\nAssistant:"
            
            # Call Gemini API
            result = self.gemini.generate_completion(
                prompt,
                system_instruction=system_instruction,
                temperature=0.7,
                max_tokens=500
            )
            
            if result['success'] and result['response']:
                answer = result['response'].strip()
                
                # Update conversation history
                self.conversation_history.append({'role': 'user', 'content': user_query})
                self.conversation_history.append({'role': 'assistant', 'content': answer})
                
                # Keep only last 10 messages
                if len(self.conversation_history) > 10:
                    self.conversation_history = self.conversation_history[-10:]
                
                return {
                    'success': True,
                    'answer': answer,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'answer': None,
                    'error': result.get('error', 'Unknown error')
                }
        
        except Exception as e:
            logger.error(f"Error answering query: {e}")
            return {
                'success': False,
                'answer': None,
                'error': str(e)
            }
    
    def summarize_email(self, email_id: int) -> Dict[str, Any]:
        """Summarize a specific email.
        
        Args:
            email_id: Email ID
            
        Returns:
            Dictionary with summary
        """
        email = self.db.get_email_by_id(email_id)
        if not email:
            return {'success': False, 'error': 'Email not found'}
        
        try:
            email_text = f"From: {email['sender']}\n"
            email_text += f"Subject: {email['subject']}\n"
            email_text += f"Body: {email['body']}\n"
            
            prompt = f"Summarize this email in 2-3 sentences, highlighting key points and any action items:\n\n{email_text}"
            
            result = self.gemini.generate_completion(prompt, max_tokens=200)
            
            if result['success'] and result['response']:
                return {
                    'success': True,
                    'summary': result['response'].strip(),
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'summary': None,
                    'error': result.get('error', 'Unknown error')
                }
        
        except Exception as e:
            logger.error(f"Error summarizing email: {e}")
            return {
                'success': False,
                'summary': None,
                'error': str(e)
            }
    
    def find_urgent_emails(self) -> List[Dict[str, Any]]:
        """Find urgent emails (Important category or high priority action items).
        
        Returns:
            List of urgent email dictionaries
        """
        important_emails = self.db.get_emails(category='Important')
        action_items = self.db.get_all_action_items(is_completed=False)
        
        urgent_emails = []
        urgent_email_ids = set()
        
        # Add important emails
        for email in important_emails:
            urgent_emails.append({
                'email': email,
                'reason': 'Marked as Important'
            })
            urgent_email_ids.add(email['id'])
        
        # Add emails with high priority action items
        for item in action_items:
            if item['priority'] == 'high' and item['email_id'] not in urgent_email_ids:
                email = self.db.get_email_by_id(item['email_id'])
                if email:
                    urgent_emails.append({
                        'email': email,
                        'reason': f"High priority task: {item['task']}"
                    })
                    urgent_email_ids.add(email['id'])
        
        return urgent_emails
    
    def list_action_items(self) -> List[Dict[str, Any]]:
        """List all pending action items.
        
        Returns:
            List of action item dictionaries with email context
        """
        action_items = self.db.get_all_action_items(is_completed=False)
        
        result = []
        for item in action_items:
            email = self.db.get_email_by_id(item['email_id'])
            result.append({
                'action_item': item,
                'email': email
            })
        
        return result
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []


