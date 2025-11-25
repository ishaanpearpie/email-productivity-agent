"""Data validation utilities for Email Productivity Agent."""

from typing import Any, Optional
from pydantic import BaseModel, validator


class EmailData(BaseModel):
    """Email data model."""
    sender: str
    subject: str
    body: str
    timestamp: str
    
    @validator('sender')
    def validate_sender(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Sender cannot be empty')
        return v.strip()
    
    @validator('subject')
    def validate_subject(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Subject cannot be empty')
        return v.strip()


class PromptData(BaseModel):
    """Prompt data model."""
    name: str
    prompt_type: str
    content: str
    
    @validator('prompt_type')
    def validate_prompt_type(cls, v):
        allowed_types = ['categorization', 'action_extraction', 'auto_reply']
        if v not in allowed_types:
            raise ValueError(f'Prompt type must be one of: {allowed_types}')
        return v
    
    @validator('content')
    def validate_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Prompt content cannot be empty')
        return v.strip()


class ActionItemData(BaseModel):
    """Action item data model."""
    task: str
    deadline: Optional[str] = None
    priority: str = 'medium'
    
    @validator('priority')
    def validate_priority(cls, v):
        allowed_priorities = ['high', 'medium', 'low']
        if v not in allowed_priorities:
            raise ValueError(f'Priority must be one of: {allowed_priorities}')
        return v


class DraftData(BaseModel):
    """Draft data model."""
    subject: str
    body: str
    email_id: Optional[int] = None
    
    @validator('subject')
    def validate_subject(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Draft subject cannot be empty')
        return v.strip()
    
    @validator('body')
    def validate_body(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Draft body cannot be empty')
        return v.strip()

