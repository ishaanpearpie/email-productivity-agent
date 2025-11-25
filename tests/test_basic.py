"""Basic tests for Email Productivity Agent."""

import pytest
import os
import tempfile
import json
from pathlib import Path

from database.db_manager import DatabaseManager
from prompts.prompt_manager import PromptManager


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db_manager = DatabaseManager(db_path=db_path)
    yield db_manager
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_database_initialization(temp_db):
    """Test database initialization."""
    assert temp_db is not None
    
    # Check if tables exist
    conn = temp_db._get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    assert 'emails' in tables
    assert 'prompts' in tables
    assert 'action_items' in tables
    assert 'drafts' in tables
    assert 'processing_logs' in tables
    
    conn.close()


def test_save_and_get_email(temp_db):
    """Test saving and retrieving emails."""
    email_id = temp_db.save_email(
        sender="test@example.com",
        subject="Test Subject",
        body="Test Body",
        timestamp="2024-01-01T00:00:00Z"
    )
    
    assert email_id is not None
    
    email = temp_db.get_email_by_id(email_id)
    assert email is not None
    assert email['sender'] == "test@example.com"
    assert email['subject'] == "Test Subject"
    assert email['body'] == "Test Body"


def test_load_mock_inbox(temp_db):
    """Test loading mock inbox."""
    # Create temporary mock inbox file
    mock_data = {
        "emails": [
            {
                "id": "test_001",
                "sender": "test@example.com",
                "sender_name": "Test User",
                "subject": "Test Email",
                "body": "Test body content",
                "timestamp": "2024-01-01T00:00:00Z",
                "has_attachments": False
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_data, f)
        temp_json_path = f.name
    
    try:
        success, message = temp_db.load_mock_inbox(temp_json_path)
        assert success is True
        assert "1" in message or "Successfully" in message
        
        emails = temp_db.get_emails()
        assert len(emails) == 1
        assert emails[0]['sender'] == "test@example.com"
    finally:
        if os.path.exists(temp_json_path):
            os.unlink(temp_json_path)


def test_prompt_manager(temp_db):
    """Test prompt manager."""
    prompt_manager = PromptManager(temp_db)
    
    # Test getting prompts
    categorization_prompt = prompt_manager.get_prompt('categorization')
    assert categorization_prompt is not None
    assert len(categorization_prompt) > 0
    
    action_prompt = prompt_manager.get_prompt('action_extraction')
    assert action_prompt is not None
    
    auto_reply_prompt = prompt_manager.get_prompt('auto_reply')
    assert auto_reply_prompt is not None


def test_save_action_item(temp_db):
    """Test saving action items."""
    # First create an email
    email_id = temp_db.save_email(
        sender="test@example.com",
        subject="Test",
        body="Test",
        timestamp="2024-01-01T00:00:00Z"
    )
    
    # Save action item
    item_id = temp_db.save_action_item(
        email_id=email_id,
        task="Test task",
        deadline="2024-01-10",
        priority="high"
    )
    
    assert item_id is not None
    
    # Get action items
    items = temp_db.get_action_items_by_email(email_id)
    assert len(items) == 1
    assert items[0]['task'] == "Test task"
    assert items[0]['priority'] == "high"


def test_save_draft(temp_db):
    """Test saving drafts."""
    draft_id = temp_db.save_draft(
        subject="Test Draft",
        body="Test body",
        email_id=None
    )
    
    assert draft_id is not None
    
    drafts = temp_db.get_drafts()
    assert len(drafts) == 1
    assert drafts[0]['subject'] == "Test Draft"


def test_email_stats(temp_db):
    """Test getting email statistics."""
    # Add some test data
    temp_db.save_email("sender1@test.com", "Subject 1", "Body 1", "2024-01-01T00:00:00Z")
    temp_db.save_email("sender2@test.com", "Subject 2", "Body 2", "2024-01-02T00:00:00Z")
    
    stats = temp_db.get_email_stats()
    assert stats['total_emails'] == 2
    assert 'category_counts' in stats
    assert 'pending_actions' in stats
    assert 'total_drafts' in stats


def test_update_email_category(temp_db):
    """Test updating email category."""
    email_id = temp_db.save_email(
        sender="test@example.com",
        subject="Test",
        body="Test",
        timestamp="2024-01-01T00:00:00Z"
    )
    
    success = temp_db.update_email_category(email_id, "Important")
    assert success is True
    
    email = temp_db.get_email_by_id(email_id)
    assert email['category'] == "Important"
    assert email['is_processed'] == 1


