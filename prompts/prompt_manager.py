"""Prompt manager for Email Productivity Agent."""

import logging
from typing import Optional, Dict, Any, List

from database.db_manager import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PromptManager:
    """Manages prompts for email processing."""
    
    # Default prompts
    DEFAULT_CATEGORIZATION_PROMPT = """Categorize this email into one of these categories: Important, Newsletter, Spam, To-Do, Project Update, Meeting Request, or General.

Rules:
- Important: Urgent matters requiring immediate attention
- To-Do: Direct requests requiring user action
- Meeting Request: Scheduling or calendar-related
- Newsletter: Bulk marketing or informational content
- Spam: Unwanted or suspicious content
- Project Update: Status reports or progress updates
- General: Everything else

Respond with ONLY the category name, nothing else."""

    DEFAULT_ACTION_EXTRACTION_PROMPT = """Extract actionable tasks from this email. For each task found, identify:
- The specific action required
- Any mentioned deadline or timeframe
- Priority level (high/medium/low)

Respond ONLY in valid JSON format:
{
  "tasks": [
    {"task": "description", "deadline": "date or timeframe", "priority": "high/medium/low"}
  ]
}

If no tasks found, return: {"tasks": []}

Do not include any markdown formatting or code blocks, just the raw JSON."""

    DEFAULT_AUTO_REPLY_PROMPT = """Generate a professional, concise email reply based on the context provided.

Guidelines:
- Match the tone of the original email
- Be polite and professional
- Keep it brief (2-3 paragraphs max)
- For meeting requests: ask for agenda and confirm availability
- For task requests: acknowledge and provide timeline
- For questions: provide clear answers or next steps

Include a subject line starting with "Re: "
Format your response as:
Subject: [subject line]
---
[email body]"""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize prompt manager.
        
        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
        self._ensure_default_prompts()
    
    def _ensure_default_prompts(self) -> None:
        """Ensure default prompts exist in database."""
        prompt_types = {
            'categorization': self.DEFAULT_CATEGORIZATION_PROMPT,
            'action_extraction': self.DEFAULT_ACTION_EXTRACTION_PROMPT,
            'auto_reply': self.DEFAULT_AUTO_REPLY_PROMPT
        }
        
        for prompt_type, content in prompt_types.items():
            existing = self.db.get_prompt_by_type(prompt_type)
            if not existing:
                self.db.save_prompt(
                    name=f"Default {prompt_type.replace('_', ' ').title()}",
                    prompt_type=prompt_type,
                    content=content
                )
                logger.info(f"Created default prompt for {prompt_type}")
    
    def get_prompt(self, prompt_type: str) -> Optional[str]:
        """Get active prompt by type.
        
        Args:
            prompt_type: Type of prompt
            
        Returns:
            Prompt content or None
        """
        prompt = self.db.get_prompt_by_type(prompt_type)
        return prompt['content'] if prompt else None
    
    def get_all_prompts(self) -> List[Dict[str, Any]]:
        """Get all active prompts.
        
        Returns:
            List of prompt dictionaries
        """
        return self.db.get_prompts()
    
    def update_prompt(self, prompt_id: int, content: str, name: Optional[str] = None) -> bool:
        """Update prompt.
        
        Args:
            prompt_id: Prompt ID
            content: New prompt content
            name: Optional new name
            
        Returns:
            True if successful
        """
        return self.db.update_prompt(prompt_id, content, name)
    
    def create_prompt(self, name: str, prompt_type: str, content: str) -> Optional[int]:
        """Create new prompt.
        
        Args:
            name: Prompt name
            prompt_type: Type of prompt
            content: Prompt content
            
        Returns:
            Prompt ID if successful
        """
        return self.db.save_prompt(name, prompt_type, content)
    
    def delete_prompt(self, prompt_id: int) -> bool:
        """Delete prompt (soft delete).
        
        Args:
            prompt_id: Prompt ID
            
        Returns:
            True if successful
        """
        return self.db.delete_prompt(prompt_id)
    
    def restore_default(self, prompt_type: str) -> bool:
        """Restore default prompt for a type.
        
        Args:
            prompt_type: Type of prompt
            
        Returns:
            True if successful
        """
        defaults = {
            'categorization': self.DEFAULT_CATEGORIZATION_PROMPT,
            'action_extraction': self.DEFAULT_ACTION_EXTRACTION_PROMPT,
            'auto_reply': self.DEFAULT_AUTO_REPLY_PROMPT
        }
        
        if prompt_type not in defaults:
            return False
        
        # Deactivate existing prompts of this type
        existing = self.db.get_prompts(prompt_type)
        for prompt in existing:
            self.db.delete_prompt(prompt['id'])
        
        # Create new default
        prompt_id = self.db.save_prompt(
            name=f"Default {prompt_type.replace('_', ' ').title()}",
            prompt_type=prompt_type,
            content=defaults[prompt_type]
        )
        
        return prompt_id is not None


