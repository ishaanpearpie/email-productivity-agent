# Email Productivity Agent - Complete Implementation

## Project Context
**Project Location**: `/home/ishaan/Downloads/Ishaan/(COLLEGE)/Company Applied/OceanAI`
**Assignment File**: `Assignment - 2.pdf` (already in project folder)

## Project Overview
Build a prompt-driven Email Productivity Agent with Streamlit UI that processes emails, categorizes them, extracts action items, and enables chat-based inbox interaction.

## Tech Stack
- **Frontend/UI**: Streamlit
- **Backend**: Python 3.11+
- **Database**: SQLite3
- **LLM Integration**: Google Gemini API (FREE - using gemini-1.5-flash or gemini-1.5-pro)
- **Key Libraries**: streamlit, google-generativeai, sqlite3, pydantic, python-dotenv, pandas

## System Architecture

### Directory Structure
```
/home/ishaan/Downloads/Ishaan/(COLLEGE)/Company Applied/OceanAI/
├── Assignment - 2.pdf      # Already exists
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── app.py                 # Main Streamlit application
├── config.py              # Configuration settings
├── database/
│   ├── __init__.py
│   ├── db_manager.py      # Database operations
│   └── schema.sql         # Database schema
├── agents/
│   ├── __init__.py
│   ├── email_processor.py # Email categorization & action extraction
│   ├── chat_agent.py      # Email Agent chat interface
│   └── draft_generator.py # Reply draft generation
├── prompts/
│   ├── __init__.py
│   └── prompt_manager.py  # Prompt CRUD operations
├── utils/
│   ├── __init__.py
│   ├── gemini_client.py   # Google Gemini API wrapper
│   └── validators.py      # Data validation
├── data/
│   ├── mock_inbox.json    # Sample emails (20 emails)
│   └── email_agent.db     # SQLite database (generated)
└── tests/
    └── test_basic.py
```

## Implementation Requirements

### Phase 1: Database & Core Setup

#### 1.1 Database Schema (database/schema.sql)
Create SQLite database with these tables:
- **emails**: id, sender, subject, body, timestamp, category, is_processed, raw_json
- **prompts**: id, name, prompt_type (categorization/action_extraction/auto_reply), content, is_active, created_at, updated_at
- **action_items**: id, email_id, task, deadline, priority, is_completed
- **drafts**: id, email_id (nullable for new emails), subject, body, metadata, created_at
- **processing_logs**: id, email_id, operation_type, status, error_message, timestamp

#### 1.2 Database Manager (database/db_manager.py)
Implement:
- `init_database()` - Create tables if not exist
- `load_mock_inbox()` - Import from mock_inbox.json
- `save_email()`, `get_emails()`, `get_email_by_id()`
- `save_prompt()`, `get_prompts()`, `get_prompt_by_type()`, `update_prompt()`, `delete_prompt()`
- `save_action_item()`, `get_action_items_by_email()`
- `save_draft()`, `get_drafts()`, `update_draft()`
- All functions should handle errors gracefully and return status/results

### Phase 2: Google Gemini Integration

#### 2.1 Gemini Client (utils/gemini_client.py)
Create a Gemini API client that:
- Uses `google-generativeai` library
- Loads API key from environment variables
- Implements `generate_completion(prompt, system_instruction, temperature, max_tokens)`
- Uses **gemini-1.5-flash** as default model (free tier, fast)
- Option to use **gemini-1.5-pro** for complex tasks
- Handles rate limiting, timeouts, and errors gracefully
- Returns structured responses with error status
- Implements retry logic (3 attempts with exponential backoff)
- Properly configures safety settings to avoid blocked responses

**Key Implementation Details:**
```python
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Configure API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Model configuration
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}

# Safety settings (permissive for business emails)
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# Initialize model
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    generation_config=generation_config,
    safety_settings=safety_settings,
    system_instruction="You are an intelligent email processing assistant."
)
```

#### 2.2 Prompt Manager (prompts/prompt_manager.py)
- Load default prompts on first run
- CRUD operations for prompts
- Validate prompt structure
- Support prompt versioning (keep history)

**Default Prompts to Create:**

1. **Categorization Prompt**:
```
Categorize this email into one of these categories: Important, Newsletter, Spam, To-Do, Project Update, Meeting Request, or General.

Rules:
- Important: Urgent matters requiring immediate attention
- To-Do: Direct requests requiring user action
- Meeting Request: Scheduling or calendar-related
- Newsletter: Bulk marketing or informational content
- Spam: Unwanted or suspicious content
- Project Update: Status reports or progress updates
- General: Everything else

Respond with ONLY the category name, nothing else.
```

2. **Action Item Extraction Prompt**:
```
Extract actionable tasks from this email. For each task found, identify:
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

Do not include any markdown formatting or code blocks, just the raw JSON.
```

3. **Auto-Reply Draft Prompt**:
```
Generate a professional, concise email reply based on the context provided.

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
[email body]
```

### Phase 3: Email Processing Agents

#### 3.1 Email Processor (agents/email_processor.py)
Implement `EmailProcessor` class:
- `categorize_email(email_content, prompt)` - Returns category
- `extract_action_items(email_content, prompt)` - Returns list of action items
- `process_inbox()` - Batch process all unprocessed emails
- Store all results in database with processing logs
- Handle Gemini API failures gracefully (mark as failed, log error)
- Parse JSON responses carefully (Gemini sometimes includes markdown)

**Important for JSON Parsing:**
- Strip markdown code blocks (```json and ```)
- Handle cases where Gemini adds extra text
- Use try-except for json.loads()
- Fallback to empty list if parsing fails

#### 3.2 Chat Agent (agents/chat_agent.py)
Implement `EmailChatAgent` class:
- `answer_query(user_query, context)` - General inbox questions
- `summarize_email(email_id)` - Summarize specific email
- `find_urgent_emails()` - Query urgent items
- `list_action_items()` - List all pending tasks
- Maintain conversation context (last 5 messages)
- Use RAG-like approach: retrieve relevant emails/prompts for context

#### 3.3 Draft Generator (agents/draft_generator.py)
Implement `DraftGenerator` class:
- `generate_reply(email_id, custom_instructions)` - Reply to specific email
- `generate_new_email(recipient, purpose, key_points)` - New email from scratch
- `refine_draft(draft_id, refinement_instructions)` - Edit existing draft
- Always use auto-reply prompt as base
- Include email context for replies
- Store as drafts, never send

### Phase 4: Streamlit UI (app.py)

#### 4.1 App Structure
Use Streamlit tabs for organization:
1. **Dashboard** - Overview stats
2. **Inbox** - Email list and viewer
3. **Prompt Manager** - Edit prompts
4. **Email Agent Chat** - Chat interface
5. **Drafts** - View/edit drafts

#### 4.2 App Initialization
```python
import streamlit as st

st.set_page_config(
    page_title="Email Productivity Agent",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    # Initialize database, load mock inbox, etc.
```

#### 4.3 Dashboard Tab
Display:
- Total emails loaded
- Breakdown by category (pie chart using `st.plotly_chart` or `st.bar_chart`)
- Number of action items pending
- Number of drafts saved
- "Process Inbox" button to run categorization on all emails
- Show processing status with progress bar

#### 4.4 Inbox Tab
Left side (30% width using `st.columns`):
- List all emails with sender, subject, timestamp
- Category badge/tag displayed using `st.badge` or colored text
- Filter by category (multiselect)
- Search by subject/sender
- Click to view details (use radio buttons or selectbox)

Right side (70% width):
- Display selected email full content
- Show extracted action items below email in expandable section
- Buttons: "Generate Reply", "Summarize", "Re-categorize"

#### 4.5 Prompt Manager Tab
For each prompt type (Categorization, Action Extraction, Auto-Reply):
- Display current prompt in `st.text_area` (editable, height=300)
- "Save Changes" button
- "Restore Default" button
- Show last updated timestamp
- "Test Prompt" feature: apply to sample email and show result
- Use `st.expander` for each prompt type

#### 4.6 Email Agent Chat Tab
- Chat interface using `st.chat_message` and `st.chat_input`
- Display conversation history from session state
- Suggested queries as `st.button`:
  - "Show me all urgent emails"
  - "What are my pending tasks?"
  - "Summarize unread emails"
  - "Find meeting requests this week"
- Show thinking/processing with `st.spinner`
- Display results in structured format (tables, lists)
- Clear chat button

#### 4.7 Drafts Tab
- List all drafts with subject, created date
- Preview draft content in expandable sections
- "Edit Draft" button (opens text area)
- "Delete Draft" button with confirmation
- "Create New Email" button (opens form with recipient, subject, body)
- Prominent warning: "⚠️ Drafts are saved locally and never automatically sent"

### Phase 5: Mock Data Generation

#### 5.1 Mock Inbox (data/mock_inbox.json)
Create 20 diverse sample emails with realistic Indian business context:

**Categories to include:**
- 3 Meeting Requests (with specific dates/times)
- 4 To-Do items (clear action items with deadlines)
- 2 Project Updates (status reports)
- 3 Newsletters (marketing content)
- 2 Spam-like messages
- 4 Important emails (urgent matters)
- 2 General emails

**Email Structure:**
```json
{
  "emails": [
    {
      "id": "email_001",
      "sender": "priya.sharma@techcorp.in",
      "sender_name": "Priya Sharma",
      "subject": "Urgent: Q4 Budget Review Meeting",
      "body": "Hi,\n\nWe need to schedule our Q4 budget review meeting. Can you join us this Friday at 2 PM IST? Please confirm your availability.\n\nBest regards,\nPriya",
      "timestamp": "2024-01-15T10:30:00Z",
      "has_attachments": false
    },
    {
      "id": "email_002",
      "sender": "noreply@newsletter.com",
      "sender_name": "Tech Weekly Digest",
      "subject": "Your Weekly AI & ML Updates - January 2024",
      "body": "Hello!\n\nHere are this week's top stories in AI and Machine Learning:\n\n1. New breakthroughs in LLM technology\n2. Google announces Gemini 2.0\n3. OpenAI releases GPT-5 beta\n\nRead more at our website...",
      "timestamp": "2024-01-14T08:00:00Z",
      "has_attachments": false
    }
  ]
}
```

**Include realistic scenarios:**
- Client requests with deadlines
- Internal team communications from Indian companies
- Conference/event invitations
- Bug reports requiring action
- Expense approval requests
- Sprint planning emails
- Password reset attempts (spam-like)
- Invoice/payment reminders

### Phase 6: Configuration & Setup

#### 6.1 Environment Configuration (.env.example)
```env
# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Model Selection (gemini-1.5-flash recommended for speed, gemini-1.5-pro for accuracy)
GEMINI_MODEL=gemini-1.5-flash

# Database
DATABASE_PATH=./data/email_agent.db

# Application Settings
DEBUG=False
AUTO_PROCESS_ON_LOAD=True
MAX_RETRIES=3
REQUEST_TIMEOUT=30
```

#### 6.2 Requirements (requirements.txt)
```
streamlit>=1.31.0
google-generativeai>=0.3.0
python-dotenv>=1.0.0
pydantic>=2.6.0
pandas>=2.2.0
plotly>=5.18.0
pytest>=8.0.0
```

#### 6.3 README.md Structure
Include:

1. **Project Overview** - Brief description and purpose
2. **Features** - Bullet list of capabilities
3. **Prerequisites** 
   - Python 3.11+
   - Google Gemini API key (FREE - get from https://makersuite.google.com/app/apikey)
4. **Installation** (Arch Linux specific):
   ```bash
   # Navigate to project directory
   cd "/home/ishaan/Downloads/Ishaan/(COLLEGE)/Company Applied/OceanAI"
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```
5. **Configuration**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env and add your Gemini API key
   nano .env
   # Add: GEMINI_API_KEY=your_actual_api_key_here
   ```
6. **Getting Gemini API Key**
   - Visit https://makersuite.google.com/app/apikey
   - Sign in with Google account
   - Click "Create API Key"
   - Copy the key to your .env file
   - Note: Free tier includes generous limits for development
7. **Usage**:
   ```bash
   # Activate virtual environment
   source venv/bin/activate
   
   # Run the application
   streamlit run app.py
   
   # Application will open in browser at http://localhost:8501
   ```
8. **Loading Mock Inbox** - Automatically loads on first run
9. **Configuring Prompts** - Use Prompt Manager tab in UI
10. **Architecture Overview** - Diagram and explanation
11. **Features Demo** - Step-by-step usage guide
12. **Safety Notes** - Drafts never auto-send, all local processing
13. **Troubleshooting**
    - API key not working: Verify key is correct in .env
    - Gemini quota exceeded: Free tier limits, wait or upgrade
    - Database locked: Close other instances of the app
    - Import errors: Ensure venv is activated

### Phase 7: Error Handling & Safety

#### 7.1 Error Handling Requirements
- Wrap all Gemini API calls in try-except blocks
- Handle specific exceptions:
  - `google.generativeai.types.BlockedPromptException`
  - `google.generativeai.types.StopCandidateException`
  - Rate limit errors
  - Network timeouts
- Display user-friendly error messages in Streamlit
- Log all errors to processing_logs table with full stack trace
- Implement fallback behaviors:
  - If categorization fails: mark as "Uncategorized"
  - If action extraction fails: empty list
  - If draft generation fails: show error, allow retry
- Display warnings for API rate limits with countdown timer

#### 7.2 Gemini-Specific Handling
- Parse responses that include markdown code blocks
- Handle cases where Gemini refuses to respond (safety filters)
- Retry with adjusted safety settings if blocked
- Strip extra formatting from JSON responses
- Validate JSON structure before parsing

#### 7.3 Safety Features
- Never implement actual email sending functionality
- Add confirmation dialogs before deleting data
- Validate all user inputs with Pydantic models
- Sanitize email content before display (prevent XSS)
- Show clear "DRAFT" labels on all generated content
- Add prominent disclaimer in UI: "⚠️ This agent generates drafts only. Review before sending."

### Phase 8: Testing & Quality

#### 8.1 Basic Tests (tests/test_basic.py)
Write pytest tests for:
- Database initialization and schema
- Mock inbox loading and parsing
- Prompt CRUD operations
- Email processing logic
- JSON parsing from Gemini responses (with malformed inputs)
- Error handling for API failures

#### 8.2 Code Quality Requirements
- Use type hints throughout (Python 3.11+ syntax)
- Add comprehensive docstrings (Google style) to all classes and functions
- Follow PEP 8 style guidelines
- Use meaningful variable names (no single letters except loop counters)
- Add inline comments for complex logic
- Maximum function length: 50 lines
- Separate concerns: UI (app.py), business logic (agents/), data access (database/)
- Use constants for magic numbers and strings

### Phase 9: Git & Version Control

#### 9.1 .gitignore
```
# Environment
.env
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Database
*.db
*.db-journal
*.sqlite
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
.directory

# Logs
*.log
logs/

# Streamlit
.streamlit/secrets.toml

# Python
*.egg-info/
dist/
build/
```

#### 9.2 Commit Strategy
Use clear, descriptive commit messages:
```
Initial commit: Project structure and requirements
Add database schema and manager
Implement Gemini API client with error handling
Add prompt manager with default templates
Implement email processor agent
Add Streamlit UI with inbox viewer
Implement chat agent functionality
Add draft generator
Create mock inbox with 20 sample emails
Write comprehensive README and documentation
Add tests and final polish
```

## Implementation Priority

**Follow this order exactly:**

1. **Database Layer** (30 mins)
   - Create schema.sql
   - Implement db_manager.py with all CRUD operations
   - Test database initialization

2. **Gemini Integration** (45 mins)
   - Create gemini_client.py
   - Implement retry logic and error handling
   - Test API calls with sample prompts
   - Handle JSON parsing edge cases

3. **Prompt System** (30 mins)
   - Create prompt_manager.py
   - Add default prompts
   - Implement CRUD operations

4. **Email Processing** (1 hour)
   - Create email_processor.py
   - Implement categorization
   - Implement action item extraction
   - Test with sample emails

5. **Streamlit UI - Phase 1** (1 hour)
   - Create app.py with basic structure
   - Add Dashboard tab
   - Add Inbox tab with email viewer
   - Add Prompt Manager tab

6. **Chat Agent** (45 mins)
   - Create chat_agent.py
   - Implement query handling
   - Add to UI

7. **Draft Generator** (45 mins)
   - Create draft_generator.py
   - Add drafts tab to UI

8. **Mock Data** (30 mins)
   - Generate mock_inbox.json with 20 emails
   - Test loading

9. **Polish & Documentation** (1 hour)
   - Write README.md
   - Add error messages
   - Test all features
   - Write tests

**Total estimated time: 6-7 hours**

## Key Implementation Notes

### Streamlit State Management
```python
# Initialize session state
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False
    st.session_state.emails = []
    st.session_state.selected_email = None
    st.session_state.chat_history = []
    st.session_state.prompts = {}
```

### Gemini Best Practices
- Use `gemini-1.5-flash` for fast, cheap operations (categorization, extraction)
- Use `gemini-1.5-pro` only if user requests higher quality
- Always set `max_output_tokens` to avoid runaway costs
- Handle safety filter blocks gracefully
- Strip markdown formatting from responses: `response.text.strip('```json\n').strip('```')`

### Streamlit Performance
- Use `@st.cache_data` for database queries that don't change often
- Use `@st.cache_resource` for Gemini model initialization
- Implement pagination for email lists (show 20 per page)
- Use `st.spinner()` for all LLM operations
- Avoid re-running expensive operations on every interaction

### Database Best Practices
- Use parameterized queries to prevent SQL injection
- Commit after each write operation
- Use transactions for batch operations
- Add indexes on frequently queried columns (sender, category, timestamp)
- Store JSON as TEXT, not BLOB

## Deliverables Checklist

- [ ] Complete source code with all modules
- [ ] SQLite database schema
- [ ] Mock inbox with 20 diverse emails
- [ ] Default prompt templates (3 types)
- [ ] Streamlit UI with all 5 tabs functional
- [ ] README.md with complete setup instructions
- [ ] requirements.txt with google-generativeai
- [ ] .env.example with Gemini configuration
- [ ] .gitignore
- [ ] Basic pytest tests
- [ ] Assignment - 2.pdf (already in folder)
- [ ] No video (will be created separately by user)

## Architecture Diagram (for README)

```
┌─────────────────────────────────────────────────┐
│         Streamlit UI (app.py)                   │
│  ┌──────────┬────────┬────────┬──────────┐     │
│  │Dashboard │ Inbox  │Prompts │   Chat   │     │
│  └──────────┴────────┴────────┴──────────┘     │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│     Business Logic (agents/)                    │
│  • EmailProcessor (categorize, extract)         │
│  • ChatAgent (answer queries)                   │
│  • DraftGenerator (create replies)              │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  LLM Client (utils/gemini_client.py)            │
│  Google Gemini API (gemini-1.5-flash)           │
│  • Free tier                                    │
│  • Fast responses                               │
│  • JSON parsing                                 │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│   Data Layer (database/db_manager.py)           │
│   SQLite Database (./data/email_agent.db)       │
│   • Emails  • Prompts  • Drafts                 │
│   • Action Items  • Processing Logs             │
└─────────────────────────────────────────────────┘
```

## Success Criteria

Your implementation is successful when:

1. ✅ Mock inbox loads and displays all 20 emails correctly
2. ✅ Users can create/edit/delete prompts through UI
3. ✅ Emails are automatically categorized using Gemini
4. ✅ Action items are extracted and stored in database
5. ✅ Chat agent answers inbox-related questions accurately
6. ✅ Drafts can be generated, edited, and saved
7. ✅ All Gemini API errors are handled gracefully with user-friendly messages
8. ✅ UI is intuitive, responsive, and visually clean
9. ✅ README provides crystal-clear setup instructions
10. ✅ Code is modular, well-documented, and follows best practices
11. ✅ No actual emails are sent (safety first!)
12. ✅ Application runs smoothly on Arch Linux

## Getting Started Command

```bash
cd "/home/ishaan/Downloads/Ishaan/(COLLEGE)/Company Applied/OceanAI"

# Start implementing in this order:
# 1. Create directory structure
# 2. Set up database (schema + manager)
# 3. Implement Gemini client
# 4. Build agents one by one
# 5. Create Streamlit UI
# 6. Generate mock data
# 7. Write documentation
```

**Important**: The Assignment - 2.pdf is already in your project folder for reference. Use Google Gemini API (free tier) for all LLM operations. Test each component as you build it. Good luck! 🚀