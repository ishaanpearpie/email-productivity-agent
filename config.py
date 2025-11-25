"""Configuration settings for Email Productivity Agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent

# Database configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', str(PROJECT_ROOT / 'data' / 'email_agent.db'))

# Gemini API configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')

# Application settings
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
AUTO_PROCESS_ON_LOAD = os.getenv('AUTO_PROCESS_ON_LOAD', 'True').lower() == 'true'
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))

# Data paths
MOCK_INBOX_PATH = PROJECT_ROOT / 'data' / 'mock_inbox.json'


