"""Draft generator for email replies and new emails."""

import logging
from typing import Optional, Dict, Any

from database.db_manager import DatabaseManager
from prompts.prompt_manager import PromptManager
from utils.gemini_client import GeminiClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DraftGenerator:
    """Generates email drafts using LLM."""
    
    def __init__(self, db_manager: DatabaseManager,
                 prompt_manager: PromptManager,
                 gemini_client: GeminiClient):
        """Initialize draft generator.
        
        Args:
            db_manager: Database manager instance
            prompt_manager: Prompt manager instance
            gemini_client: Gemini API client instance
        """
        self.db = db_manager
        self.prompt_manager = prompt_manager
        self.gemini = gemini_client
    
    def generate_reply(self, email_id: int, 
                      custom_instructions: Optional[str] = None) -> Dict[str, Any]:
        """Generate reply draft for an email.
        
        Args:
            email_id: Email ID to reply to
            custom_instructions: Optional custom instructions for the reply
            
        Returns:
            Dictionary with draft subject and body
        """
        email = self.db.get_email_by_id(email_id)
        if not email:
            return {'success': False, 'error': 'Email not found'}
        
        try:
            # Get auto-reply prompt
            prompt = self.prompt_manager.get_prompt('auto_reply')
            if not prompt:
                return {'success': False, 'error': 'No auto-reply prompt found'}
            
            # Build email context
            email_context = f"Original Email:\n"
            email_context += f"From: {email['sender']}\n"
            email_context += f"Subject: {email['subject']}\n"
            email_context += f"Body: {email['body']}\n"
            
            # Add custom instructions if provided
            if custom_instructions:
                email_context += f"\nCustom Instructions: {custom_instructions}\n"
            
            # Build full prompt
            full_prompt = f"{prompt}\n\n{email_context}"
            
            # Call Gemini API
            result = self.gemini.generate_completion(
                full_prompt,
                temperature=0.8,
                max_tokens=1000
            )
            
            if result['success'] and result['response']:
                response_text = result['response'].strip()
                
                # Parse subject and body
                subject = ""
                body = ""
                
                if "Subject:" in response_text:
                    parts = response_text.split("Subject:", 1)
                    if len(parts) > 1:
                        subject_part = parts[1].split("---", 1)[0].strip()
                        subject = subject_part.replace("Re: ", "").strip()
                        
                        if "---" in response_text:
                            body = response_text.split("---", 1)[1].strip()
                        else:
                            body = response_text.split(subject_part, 1)[1].strip() if len(parts) > 1 else response_text
                else:
                    # Fallback: use original subject with Re: prefix
                    subject = f"Re: {email['subject']}"
                    body = response_text
                
                # Save draft
                draft_id = self.db.save_draft(
                    subject=subject,
                    body=body,
                    email_id=email_id,
                    metadata=f"Generated reply for email {email_id}"
                )
                
                return {
                    'success': True,
                    'draft_id': draft_id,
                    'subject': subject,
                    'body': body,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'draft_id': None,
                    'subject': None,
                    'body': None,
                    'error': result.get('error', 'Unknown error')
                }
        
        except Exception as e:
            logger.error(f"Error generating reply: {e}")
            return {
                'success': False,
                'draft_id': None,
                'subject': None,
                'body': None,
                'error': str(e)
            }
    
    def generate_new_email(self, recipient: str, purpose: str,
                          key_points: Optional[str] = None) -> Dict[str, Any]:
        """Generate new email draft from scratch.
        
        Args:
            recipient: Recipient email address
            purpose: Purpose of the email
            key_points: Optional key points to include
            
        Returns:
            Dictionary with draft subject and body
        """
        try:
            prompt = f"""Generate a professional email with the following requirements:

Recipient: {recipient}
Purpose: {purpose}
{f"Key Points to Include: {key_points}" if key_points else ""}

Guidelines:
- Create an appropriate subject line
- Write a professional, concise email body (2-3 paragraphs)
- Match the tone to the purpose
- Be clear and direct

Format your response as:
Subject: [subject line]
---
[email body]"""
            
            # Call Gemini API
            result = self.gemini.generate_completion(
                prompt,
                temperature=0.8,
                max_tokens=1000
            )
            
            if result['success'] and result['response']:
                response_text = result['response'].strip()
                
                # Parse subject and body
                subject = ""
                body = ""
                
                if "Subject:" in response_text:
                    parts = response_text.split("Subject:", 1)
                    if len(parts) > 1:
                        subject_part = parts[1].split("---", 1)[0].strip()
                        subject = subject_part.strip()
                        
                        if "---" in response_text:
                            body = response_text.split("---", 1)[1].strip()
                        else:
                            body = response_text.split(subject_part, 1)[1].strip() if len(parts) > 1 else response_text
                else:
                    # Fallback
                    subject = purpose[:50]  # Use purpose as subject
                    body = response_text
                
                # Save draft
                draft_id = self.db.save_draft(
                    subject=subject,
                    body=body,
                    email_id=None,
                    metadata=f"New email to {recipient}"
                )
                
                return {
                    'success': True,
                    'draft_id': draft_id,
                    'subject': subject,
                    'body': body,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'draft_id': None,
                    'subject': None,
                    'body': None,
                    'error': result.get('error', 'Unknown error')
                }
        
        except Exception as e:
            logger.error(f"Error generating new email: {e}")
            return {
                'success': False,
                'draft_id': None,
                'subject': None,
                'body': None,
                'error': str(e)
            }
    
    def refine_draft(self, draft_id: int, 
                    refinement_instructions: str) -> Dict[str, Any]:
        """Refine an existing draft.
        
        Args:
            draft_id: Draft ID
            refinement_instructions: Instructions for refinement
            
        Returns:
            Dictionary with updated draft
        """
        drafts = self.db.get_drafts()
        draft = next((d for d in drafts if d['id'] == draft_id), None)
        
        if not draft:
            return {'success': False, 'error': 'Draft not found'}
        
        try:
            prompt = f"""Refine this email draft based on the following instructions:

Original Draft:
Subject: {draft['subject']}
Body: {draft['body']}

Refinement Instructions: {refinement_instructions}

Provide the refined email in the same format:
Subject: [subject line]
---
[email body]"""
            
            # Call Gemini API
            result = self.gemini.generate_completion(
                prompt,
                temperature=0.8,
                max_tokens=1000
            )
            
            if result['success'] and result['response']:
                response_text = result['response'].strip()
                
                # Parse subject and body
                subject = draft['subject']  # Default to original
                body = draft['body']  # Default to original
                
                if "Subject:" in response_text:
                    parts = response_text.split("Subject:", 1)
                    if len(parts) > 1:
                        subject_part = parts[1].split("---", 1)[0].strip()
                        subject = subject_part.strip()
                        
                        if "---" in response_text:
                            body = response_text.split("---", 1)[1].strip()
                        else:
                            body = response_text.split(subject_part, 1)[1].strip() if len(parts) > 1 else response_text
                
                # Update draft
                success = self.db.update_draft(draft_id, subject, body)
                
                return {
                    'success': success,
                    'subject': subject,
                    'body': body,
                    'error': None if success else 'Failed to update draft'
                }
            else:
                return {
                    'success': False,
                    'subject': None,
                    'body': None,
                    'error': result.get('error', 'Unknown error')
                }
        
        except Exception as e:
            logger.error(f"Error refining draft: {e}")
            return {
                'success': False,
                'subject': None,
                'body': None,
                'error': str(e)
            }


