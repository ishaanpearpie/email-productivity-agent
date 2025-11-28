"""Database manager for Email Productivity Agent."""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from config import DATABASE_PATH

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages all database operations for the Email Productivity Agent."""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_data_dir()
        self.init_database()
    
    def _ensure_data_dir(self) -> None:
        """Ensure data directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection.
        
        Returns:
            SQLite connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self) -> bool:
        """Initialize database with schema.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            schema_path = Path(__file__).parent / 'schema.sql'
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.executescript(schema_sql)
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False
    
    def load_mock_inbox(self, json_path: str) -> Tuple[bool, str]:
        """Load emails from mock inbox JSON file.
        
        Args:
            json_path: Path to mock_inbox.json file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            emails = data.get('emails', [])
            if not emails:
                return False, "No emails found in JSON file"
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check if emails already exist in database
            cursor.execute("SELECT COUNT(*) as count FROM emails")
            existing_count = cursor.fetchone()['count']
            
            if existing_count > 0:
                conn.close()
                return False, f"Emails already loaded ({existing_count} emails in database). Clear database first if you want to reload."
            
            loaded_count = 0
            for email_data in emails:
                try:
                    # Check for duplicate by checking sender+subject+timestamp combination
                    cursor.execute("""
                        SELECT id FROM emails 
                        WHERE sender = ? AND subject = ? AND timestamp = ?
                    """, (
                        email_data.get('sender', ''),
                        email_data.get('subject', ''),
                        email_data.get('timestamp', datetime.now().isoformat())
                    ))
                    
                    if cursor.fetchone():
                        logger.debug(f"Email already exists: {email_data.get('subject')}")
                        continue
                    
                    cursor.execute("""
                        INSERT INTO emails (sender, subject, body, timestamp, raw_json)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        email_data.get('sender', ''),
                        email_data.get('subject', ''),
                        email_data.get('body', ''),
                        email_data.get('timestamp', datetime.now().isoformat()),
                        json.dumps(email_data)
                    ))
                    loaded_count += 1
                except sqlite3.IntegrityError as e:
                    logger.warning(f"Error inserting email {email_data.get('id')}: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            message = f"Successfully loaded {loaded_count} emails from mock inbox"
            logger.info(message)
            return True, message
        except FileNotFoundError:
            return False, f"Mock inbox file not found: {json_path}"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {e}"
        except Exception as e:
            logger.error(f"Error loading mock inbox: {e}")
            return False, f"Error loading mock inbox: {e}"
    
    def save_email(self, sender: str, subject: str, body: str, 
                   timestamp: str, raw_json: Optional[str] = None) -> Optional[int]:
        """Save email to database.
        
        Args:
            sender: Email sender address
            subject: Email subject
            body: Email body content
            timestamp: Email timestamp (ISO format)
            raw_json: Optional raw JSON data
            
        Returns:
            Email ID if successful, None otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO emails (sender, subject, body, timestamp, raw_json)
                VALUES (?, ?, ?, ?, ?)
            """, (sender, subject, body, timestamp, raw_json))
            email_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return email_id
        except Exception as e:
            logger.error(f"Error saving email: {e}")
            return None
    
    def get_emails(self, category: Optional[str] = None, 
                   is_processed: Optional[bool] = None,
                   limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get emails from database.
        
        Args:
            category: Filter by category
            is_processed: Filter by processed status
            limit: Maximum number of emails to return
            
        Returns:
            List of email dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM emails WHERE 1=1"
            params = []
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            if is_processed is not None:
                query += " AND is_processed = ?"
                params.append(1 if is_processed else 0)
            
            query += " ORDER BY timestamp DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting emails: {e}")
            return []
    
    def get_email_by_id(self, email_id: int) -> Optional[Dict[str, Any]]:
        """Get email by ID.
        
        Args:
            email_id: Email ID
            
        Returns:
            Email dictionary or None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM emails WHERE id = ?", (email_id,))
            row = cursor.fetchone()
            conn.close()
            
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting email by ID: {e}")
            return None
    
    def update_email_category(self, email_id: int, category: str) -> bool:
        """Update email category.
        
        Args:
            email_id: Email ID
            category: New category
            
        Returns:
            True if successful
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE emails 
                SET category = ?, is_processed = 1 
                WHERE id = ?
            """, (category, email_id))
            rows_updated = cursor.rowcount
            conn.commit()
            conn.close()
            
            if rows_updated == 0:
                logger.warning(f"No email found with id {email_id} to update category")
                return False
            
            logger.info(f"Updated email {email_id} category to: {category}")
            return True
        except Exception as e:
            logger.error(f"Error updating email category: {e}")
            return False
    
    def reset_processed_flag(self, email_id: Optional[int] = None) -> int:
        """Reset is_processed flag for emails (allows reprocessing).
        
        Args:
            email_id: Optional specific email ID, or None for all emails
            
        Returns:
            Number of emails updated
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if email_id:
                cursor.execute("""
                    UPDATE emails 
                    SET is_processed = 0 
                    WHERE id = ?
                """, (email_id,))
            else:
                cursor.execute("""
                    UPDATE emails 
                    SET is_processed = 0
                """)
            
            rows_updated = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Reset processed flag for {rows_updated} email(s)")
            return rows_updated
        except Exception as e:
            logger.error(f"Error resetting processed flag: {e}")
            return 0
    
    def save_prompt(self, name: str, prompt_type: str, content: str) -> Optional[int]:
        """Save prompt to database.
        
        Args:
            name: Prompt name
            prompt_type: Type of prompt (categorization/action_extraction/auto_reply)
            content: Prompt content
            
        Returns:
            Prompt ID if successful, None otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO prompts (name, prompt_type, content)
                VALUES (?, ?, ?)
            """, (name, prompt_type, content))
            prompt_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return prompt_id
        except Exception as e:
            logger.error(f"Error saving prompt: {e}")
            return None
    
    def get_prompts(self, prompt_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get prompts from database.
        
        Args:
            prompt_type: Filter by prompt type
            
        Returns:
            List of prompt dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if prompt_type:
                cursor.execute("""
                    SELECT * FROM prompts 
                    WHERE prompt_type = ? AND is_active = 1
                    ORDER BY updated_at DESC
                """, (prompt_type,))
            else:
                cursor.execute("""
                    SELECT * FROM prompts 
                    WHERE is_active = 1
                    ORDER BY updated_at DESC
                """)
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting prompts: {e}")
            return []
    
    def get_prompt_by_type(self, prompt_type: str) -> Optional[Dict[str, Any]]:
        """Get active prompt by type.
        
        Args:
            prompt_type: Type of prompt
            
        Returns:
            Prompt dictionary or None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM prompts 
                WHERE prompt_type = ? AND is_active = 1
                ORDER BY updated_at DESC
                LIMIT 1
            """, (prompt_type,))
            row = cursor.fetchone()
            conn.close()
            
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting prompt by type: {e}")
            return None
    
    def update_prompt(self, prompt_id: int, content: str, name: Optional[str] = None) -> bool:
        """Update prompt.
        
        Args:
            prompt_id: Prompt ID
            content: New prompt content
            name: Optional new name
            
        Returns:
            True if successful
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if name:
                cursor.execute("""
                    UPDATE prompts 
                    SET content = ?, name = ?, updated_at = datetime('now')
                    WHERE id = ?
                """, (content, name, prompt_id))
            else:
                cursor.execute("""
                    UPDATE prompts 
                    SET content = ?, updated_at = datetime('now')
                    WHERE id = ?
                """, (content, prompt_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating prompt: {e}")
            return False
    
    def delete_prompt(self, prompt_id: int) -> bool:
        """Delete prompt (soft delete by setting is_active = 0).
        
        Args:
            prompt_id: Prompt ID
            
        Returns:
            True if successful
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE prompts 
                SET is_active = 0 
                WHERE id = ?
            """, (prompt_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error deleting prompt: {e}")
            return False
    
    def save_action_item(self, email_id: int, task: str, 
                        deadline: Optional[str] = None,
                        priority: str = 'medium') -> Optional[int]:
        """Save action item.
        
        Args:
            email_id: Associated email ID
            task: Task description
            deadline: Optional deadline
            priority: Priority level (high/medium/low)
            
        Returns:
            Action item ID if successful, None otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO action_items (email_id, task, deadline, priority)
                VALUES (?, ?, ?, ?)
            """, (email_id, task, deadline, priority))
            item_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return item_id
        except Exception as e:
            logger.error(f"Error saving action item: {e}")
            return None
    
    def get_action_items_by_email(self, email_id: int) -> List[Dict[str, Any]]:
        """Get action items for an email.
        
        Args:
            email_id: Email ID
            
        Returns:
            List of action item dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM action_items 
                WHERE email_id = ? AND is_completed = 0
                ORDER BY 
                    CASE priority 
                        WHEN 'high' THEN 1 
                        WHEN 'medium' THEN 2 
                        WHEN 'low' THEN 3 
                    END,
                    deadline ASC
            """, (email_id,))
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting action items: {e}")
            return []
    
    def get_all_action_items(self, is_completed: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get all action items.
        
        Args:
            is_completed: Filter by completion status
            
        Returns:
            List of action item dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if is_completed is not None:
                cursor.execute("""
                    SELECT * FROM action_items 
                    WHERE is_completed = ?
                    ORDER BY 
                        CASE priority 
                            WHEN 'high' THEN 1 
                            WHEN 'medium' THEN 2 
                            WHEN 'low' THEN 3 
                        END,
                        deadline ASC
                """, (1 if is_completed else 0,))
            else:
                cursor.execute("""
                    SELECT * FROM action_items 
                    ORDER BY 
                        CASE priority 
                            WHEN 'high' THEN 1 
                            WHEN 'medium' THEN 2 
                            WHEN 'low' THEN 3 
                        END,
                        deadline ASC
                """)
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting all action items: {e}")
            return []
    
    def save_draft(self, subject: str, body: str, 
                   email_id: Optional[int] = None,
                   metadata: Optional[str] = None) -> Optional[int]:
        """Save draft.
        
        Args:
            subject: Draft subject
            body: Draft body
            email_id: Optional associated email ID
            metadata: Optional metadata JSON string
            
        Returns:
            Draft ID if successful, None otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO drafts (email_id, subject, body, metadata)
                VALUES (?, ?, ?, ?)
            """, (email_id, subject, body, metadata))
            draft_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return draft_id
        except Exception as e:
            logger.error(f"Error saving draft: {e}")
            return None
    
    def get_drafts(self) -> List[Dict[str, Any]]:
        """Get all drafts.
        
        Returns:
            List of draft dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM drafts 
                ORDER BY updated_at DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting drafts: {e}")
            return []
    
    def update_draft(self, draft_id: int, subject: str, body: str) -> bool:
        """Update draft.
        
        Args:
            draft_id: Draft ID
            subject: New subject
            body: New body
            
        Returns:
            True if successful
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE drafts 
                SET subject = ?, body = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (subject, body, draft_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating draft: {e}")
            return False
    
    def delete_draft(self, draft_id: int) -> bool:
        """Delete draft.
        
        Args:
            draft_id: Draft ID
            
        Returns:
            True if successful
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error deleting draft: {e}")
            return False
    
    def log_processing(self, email_id: Optional[int], operation_type: str,
                      status: str, error_message: Optional[str] = None) -> Optional[int]:
        """Log processing operation.
        
        Args:
            email_id: Optional email ID
            operation_type: Type of operation
            status: Status (success/failed/pending)
            error_message: Optional error message
            
        Returns:
            Log ID if successful, None otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO processing_logs (email_id, operation_type, status, error_message)
                VALUES (?, ?, ?, ?)
            """, (email_id, operation_type, status, error_message))
            log_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return log_id
        except Exception as e:
            logger.error(f"Error logging processing: {e}")
            return None
    
    def get_email_stats(self) -> Dict[str, Any]:
        """Get email statistics.
        
        Returns:
            Dictionary with email statistics
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Total emails
            cursor.execute("SELECT COUNT(*) as count FROM emails")
            total_emails = cursor.fetchone()['count']
            
            # By category
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM emails 
                GROUP BY category
            """)
            category_counts = {row['category']: row['count'] for row in cursor.fetchall()}
            
            # Pending action items
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM action_items 
                WHERE is_completed = 0
            """)
            pending_actions = cursor.fetchone()['count']
            
            # Total drafts
            cursor.execute("SELECT COUNT(*) as count FROM drafts")
            total_drafts = cursor.fetchone()['count']
            
            conn.close()
            
            return {
                'total_emails': total_emails,
                'category_counts': category_counts,
                'pending_actions': pending_actions,
                'total_drafts': total_drafts
            }
        except Exception as e:
            logger.error(f"Error getting email stats: {e}")
            return {
                'total_emails': 0,
                'category_counts': {},
                'pending_actions': 0,
                'total_drafts': 0
            }


