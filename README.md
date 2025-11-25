# Email Productivity Agent

An intelligent email management system powered by Google Gemini AI that helps you categorize emails, extract action items, generate replies, and interact with your inbox through a natural chat interface.

##  Features

- ** Email Categorization**: Automatically categorize emails into Important, Newsletter, Spam, To-Do, Project Update, Meeting Request, or General
- ** Action Item Extraction**: Extract actionable tasks with deadlines and priorities from emails
- ** Chat Interface**: Ask questions about your inbox and get intelligent answers
- ** Draft Generation**: Generate professional email replies and new emails using AI
- ** Prompt Management**: Customize and manage prompts for categorization, action extraction, and auto-reply
- ** Dashboard**: Visual overview of your inbox with statistics and category breakdown
- ** Smart Search**: Search and filter emails by category, sender, or subject

##  Architecture

```
┌─────────────────────────────────────────────────┐
│         Streamlit UI (app.py)                   │
│  ┌──────────┬────────┬────────┬──────────┐      │
│  │Dashboard │ Inbox  │Prompts │   Chat   │      │
│  └──────────┴────────┴────────┴──────────┘      │
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

##  Prerequisites

- **Python 3.11+**
- **Google Gemini API Key** (FREE - get from https://makersuite.google.com/app/apikey)

##  Installation

### 1. Navigate to Project Directory

```bash
cd "/home/ishaan/Downloads/Ishaan/(COLLEGE)/Company Applied/OceanAI"
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install dependencies
pip install -r requirements.txt
```

### 4. Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your Gemini API key
nano .env
# Add: GEMINI_API_KEY=your_actual_api_key_here
```

##  Getting Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key to your `.env` file
5. **Note**: Free tier includes generous limits for development

##  Usage

### Run the Application

```bash
# Activate virtual environment (if not already activated)
source venv/bin/activate

# Run the application
streamlit run app.py

# Application will open in browser at http://localhost:8501
```

### Loading Mock Inbox

The application automatically loads the mock inbox (`data/mock_inbox.json`) on first run. This includes 20 diverse sample emails covering various categories.

### Processing Emails

1. Go to the **Dashboard** tab
2. Click **" Process Inbox"** to categorize all emails and extract action items
3. View processing progress and results

### Using the Chat Agent

1. Navigate to the **Email Agent Chat** tab
2. Ask questions like:
   - "Show me all urgent emails"
   - "What are my pending tasks?"
   - "Summarize unread emails"
   - "Find meeting requests this week"
3. Or type your own questions about your inbox

### Generating Drafts

1. **Reply to Email**: 
   - Go to **Inbox** tab
   - Select an email
   - Click **" Generate Reply"**
   - Draft will be saved in **Drafts** tab

2. **Create New Email**:
   - Go to **Drafts** tab
   - Click **" Create New Email"**
   - Fill in recipient, purpose, and key points
   - Click **" Generate Draft"**

### Managing Prompts

1. Go to **Prompt Manager** tab
2. Edit prompts for:
   - **Categorization**: How emails are categorized
   - **Action Extraction**: How action items are extracted
   - **Auto-Reply**: How reply drafts are generated
3. Test prompts before saving
4. Restore defaults if needed

##  Project Structure

```
OceanAI/
├── Assignment - 2.pdf          # Assignment document
├── README.md                    # This file
├── requirements.txt            # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── app.py                       # Main Streamlit application
├── config.py                    # Configuration settings
├── database/
│   ├── __init__.py
│   ├── db_manager.py           # Database operations
│   └── schema.sql              # Database schema
├── agents/
│   ├── __init__.py
│   ├── email_processor.py      # Email categorization & action extraction
│   ├── chat_agent.py           # Email Agent chat interface
│   └── draft_generator.py       # Reply draft generation
├── prompts/
│   ├── __init__.py
│   └── prompt_manager.py       # Prompt CRUD operations
├── utils/
│   ├── __init__.py
│   ├── gemini_client.py        # Google Gemini API wrapper
│   └── validators.py           # Data validation
├── data/
│   ├── mock_inbox.json         # Sample emails (20 emails)
│   └── email_agent.db          # SQLite database (generated)
└── tests/
    └── test_basic.py            # Basic tests
```

## 🎨 Features Demo

### Dashboard
- View total emails, pending actions, and drafts
- See category breakdown with pie chart
- Process entire inbox with one click

### Inbox
- Browse all emails with search and filter
- View email details with category badges
- See extracted action items
- Generate replies, summarize, or re-categorize

### Prompt Manager
- Edit prompts for different operations
- Test prompts on sample emails
- Restore default prompts
- View last updated timestamps

### Email Agent Chat
- Natural language queries about inbox
- Suggested queries for common tasks
- Conversation history
- Find urgent emails and pending tasks

### Drafts
- View all generated drafts
- Edit drafts manually
- Refine drafts with AI
- Create new emails from scratch
- **⚠️ Important**: Drafts are never automatically sent

## ⚠️ Safety Notes

- **Drafts Never Auto-Send**: All generated drafts are saved locally and require manual review before sending
- **Local Processing**: All data is stored locally in SQLite database
- **API Key Security**: Never commit your `.env` file with API keys
- **Error Handling**: All Gemini API errors are handled gracefully with user-friendly messages

##  Troubleshooting

### API Key Not Working
- Verify key is correct in `.env` file
- Ensure key is from [Google AI Studio](https://makersuite.google.com/app/apikey)
- Check for typos or extra spaces

### Gemini Quota Exceeded
- Free tier has rate limits
- Wait a few minutes and try again
- Consider upgrading to paid tier for higher limits

### Database Locked
- Close other instances of the app
- Delete `data/email_agent.db-journal` if it exists
- Restart the application

### Import Errors
- Ensure virtual environment is activated: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.11+)

### Mock Inbox Not Loading
- Check that `data/mock_inbox.json` exists
- Verify JSON format is valid
- Check file permissions

## 🧪 Testing

Run basic tests:

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
pytest tests/
```

##  Configuration Options

Edit `.env` file to customize:

- `GEMINI_MODEL`: Choose between `gemini-1.5-flash` (fast) or `gemini-1.5-pro` (accurate)
- `MAX_RETRIES`: Number of retry attempts for API calls (default: 3)
- `REQUEST_TIMEOUT`: API request timeout in seconds (default: 30)
- `AUTO_PROCESS_ON_LOAD`: Automatically process emails on load (default: True)

##  Contributing

This is an assignment project. For improvements:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

##  License

This project is created for educational/assignment purposes.

##  Acknowledgments

- Google Gemini API for LLM capabilities
- Streamlit for the UI framework
- SQLite for lightweight database

##  Support

For issues or questions:
1. Check the Troubleshooting section
2. Review error messages in the UI
3. Check processing logs in the database

---

**Built with  using Google Gemini AI and Streamlit**


