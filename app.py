"""Main Streamlit application for Email Productivity Agent."""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from pathlib import Path

from config import DATABASE_PATH, MOCK_INBOX_PATH
from database.db_manager import DatabaseManager
from prompts.prompt_manager import PromptManager
from utils.gemini_client import GeminiClient
from agents.email_processor import EmailProcessor
from agents.chat_agent import EmailChatAgent
from agents.draft_generator import DraftGenerator

# Page configuration
st.set_page_config(
    page_title="Email Productivity Agent",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.db_manager = None
    st.session_state.prompt_manager = None
    st.session_state.gemini_client = None
    st.session_state.email_processor = None
    st.session_state.chat_agent = None
    st.session_state.draft_generator = None
    st.session_state.selected_email = None
    st.session_state.chat_history = []
    st.session_state.mock_loaded = False


def initialize_app():
    """Initialize application components."""
    try:
        # Initialize database
        db_manager = DatabaseManager()
        
        # Check if mock inbox needs to be loaded
        # Only load if no emails exist in database
        existing_emails = db_manager.get_emails()
        if not st.session_state.mock_loaded and len(existing_emails) == 0:
            if MOCK_INBOX_PATH.exists():
                success, message = db_manager.load_mock_inbox(str(MOCK_INBOX_PATH))
                if success:
                    st.session_state.mock_loaded = True
                    st.success(message)
                else:
                    # If loading failed but not because of existing emails, show warning
                    if "already loaded" not in message:
                        st.warning(message)
        elif len(existing_emails) > 0:
            # Emails already exist, mark as loaded
            st.session_state.mock_loaded = True
        
        # Initialize Gemini client
        try:
            gemini_client = GeminiClient()
        except ValueError as e:
            st.error(f"⚠️ Gemini API Key not configured: {e}")
            st.info("Please set GEMINI_API_KEY in your .env file")
            st.stop()
        
        # Initialize managers and agents
        prompt_manager = PromptManager(db_manager)
        email_processor = EmailProcessor(db_manager, prompt_manager, gemini_client)
        chat_agent = EmailChatAgent(db_manager, gemini_client)
        draft_generator = DraftGenerator(db_manager, prompt_manager, gemini_client)
        
        # Store in session state
        st.session_state.db_manager = db_manager
        st.session_state.prompt_manager = prompt_manager
        st.session_state.gemini_client = gemini_client
        st.session_state.email_processor = email_processor
        st.session_state.chat_agent = chat_agent
        st.session_state.draft_generator = draft_generator
        st.session_state.initialized = True
        
        return True
    except Exception as e:
        st.error(f"Error initializing application: {e}")
        return False


# Initialize app
if not st.session_state.initialized:
    with st.spinner("Initializing Email Productivity Agent..."):
        initialize_app()

if not st.session_state.initialized:
    st.stop()

# Main app
db = st.session_state.db_manager
prompt_manager = st.session_state.prompt_manager
email_processor = st.session_state.email_processor
chat_agent = st.session_state.chat_agent
draft_generator = st.session_state.draft_generator

# Sidebar
with st.sidebar:
    st.title("📧 Email Agent")
    st.markdown("---")
    st.markdown("⚠️ **Important**: Drafts are saved locally and never automatically sent.")
    
    # Quick stats
    stats = db.get_email_stats()
    st.metric("Total Emails", stats['total_emails'])
    st.metric("Pending Actions", stats['pending_actions'])
    st.metric("Drafts", stats['total_drafts'])

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard", "📬 Inbox", "⚙️ Prompt Manager", 
    "💬 Email Agent Chat", "📝 Drafts"
])

# Dashboard Tab
with tab1:
    st.header("📊 Dashboard")
    
    # Stats overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Emails", stats['total_emails'])
    with col2:
        st.metric("Pending Actions", stats['pending_actions'])
    with col3:
        st.metric("Drafts", stats['total_drafts'])
    with col4:
        processed = len(db.get_emails(is_processed=True))
        st.metric("Processed", f"{processed}/{stats['total_emails']}")
    
    st.markdown("---")
    
    # Category breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Email Categories")
        if stats['category_counts']:
            category_df = pd.DataFrame([
                {'Category': k, 'Count': v} 
                for k, v in stats['category_counts'].items()
            ])
            
            if not category_df.empty:
                fig = px.pie(
                    category_df, 
                    values='Count', 
                    names='Category',
                    title="Email Distribution by Category"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No categorized emails yet")
        else:
            st.info("No categorized emails yet")
    
    with col2:
        st.subheader("Actions")
        
        # Processing options
        st.markdown("**Processing Options:**")
        processing_mode = st.radio(
            "Choose processing mode:",
            ["Fast (Categorize only)", "Full (Categorize + Extract Actions)"],
            index=0,  # Default to Fast mode
            horizontal=True,
            key="processing_mode",
            help="Fast mode is recommended - categorizes emails quickly. Full mode also extracts action items but takes longer."
        )
        
        col_process1, col_process2 = st.columns(2)
        
        with col_process1:
            if st.button("🔄 Process Inbox", type="primary", use_container_width=True):
                skip_actions = (processing_mode == "Fast (Categorize only)")
                
                # Get unprocessed count
                unprocessed = db.get_emails(is_processed=False)
                total = len(unprocessed)
                
                if total == 0:
                    st.info("No unprocessed emails found. Click 'Force Reprocess All' first.")
                else:
                    # Create progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    def update_progress(current, total_emails, email_subject):
                        """Update progress callback."""
                        progress = current / total_emails
                        progress_bar.progress(progress)
                        status_text.text(f"Processing {current}/{total_emails}: {email_subject[:50]}...")
                    
                    try:
                        result = email_processor.process_inbox(
                            progress_callback=update_progress,
                            skip_action_extraction=skip_actions
                        )
                        
                        progress_bar.progress(1.0)
                        
                        if result['success']:
                            if result.get('message'):
                                st.info(result['message'])
                            else:
                                status_text.text(f"✅ Processed {result['processed']}/{result['total']} emails successfully")
                                if result['failed'] > 0:
                                    st.warning(f"⚠️ {result['failed']} emails failed to process")
                                    if result.get('errors'):
                                        with st.expander("View errors"):
                                            for error in result['errors']:
                                                st.text(error)
                        else:
                            st.error("Failed to process inbox")
                    except Exception as e:
                        st.error(f"Error during processing: {e}")
                        logger.exception("Processing error")
                    finally:
                        st.rerun()
        
        with col_process2:
            if st.button("🔄 Force Reprocess All", use_container_width=True):
                with st.spinner("Resetting emails for reprocessing..."):
                    count = db.reset_processed_flag()
                    st.info(f"Reset {count} emails. Click 'Process Inbox' to categorize them.")
                    st.rerun()
        
        if st.button("🔄 Refresh Stats", use_container_width=True):
            st.rerun()

# Inbox Tab
with tab2:
    st.header("📬 Inbox")
    
    # Filters
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input("🔍 Search", placeholder="Search by subject or sender...")
    
    with col2:
        all_categories = ['All'] + list(stats['category_counts'].keys())
        selected_category = st.selectbox("Category", all_categories)
    
    # Get emails
    emails = db.get_emails()
    
    # Apply filters
    if search_query:
        emails = [e for e in emails if search_query.lower() in e['subject'].lower() 
                 or search_query.lower() in e['sender'].lower()]
    
    if selected_category != 'All':
        emails = [e for e in emails if e['category'] == selected_category]
    
    # Email list and viewer
    col1, col2 = st.columns([3, 7])
    
    with col1:
        st.subheader("Email List")
        
        if not emails:
            st.info("No emails found")
        else:
            # Email selection
            email_options = {
                f"{e['subject'][:50]}... ({e['sender']})": e['id'] 
                for e in emails
            }
            
            selected_email_key = st.radio(
                "Select email",
                options=list(email_options.keys()),
                key="email_selector"
            )
            
            selected_email_id = email_options[selected_email_key]
            selected_email = db.get_email_by_id(selected_email_id)
            st.session_state.selected_email = selected_email
    
    with col2:
        st.subheader("Email Details")
        
        if st.session_state.selected_email:
            email = st.session_state.selected_email
            
            # Email header
            st.markdown(f"**From:** {email['sender']}")
            st.markdown(f"**Subject:** {email['subject']}")
            st.markdown(f"**Date:** {email['timestamp']}")
            
            # Category badge
            category_colors = {
                'Important': '🔴',
                'To-Do': '🟡',
                'Meeting Request': '🔵',
                'Project Update': '🟢',
                'Newsletter': '⚪',
                'Spam': '⚫',
                'General': '⚪',
                'Uncategorized': '⚪'
            }
            category_icon = category_colors.get(email['category'], '⚪')
            st.markdown(f"**Category:** {category_icon} {email['category']}")
            
            st.markdown("---")
            
            # Email body
            st.markdown("**Body:**")
            st.text_area("", email['body'], height=200, disabled=True, key="email_body")
            
            # Action items
            action_items = db.get_action_items_by_email(email['id'])
            if action_items:
                with st.expander(f"📋 Action Items ({len(action_items)})", expanded=True):
                    for item in action_items:
                        priority_colors = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                        priority_icon = priority_colors.get(item['priority'], '⚪')
                        st.markdown(f"{priority_icon} **{item['task']}**")
                        if item['deadline']:
                            st.caption(f"Deadline: {item['deadline']}")
            
            # Actions
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✉️ Generate Reply", use_container_width=True):
                    with st.spinner("Generating reply..."):
                        result = draft_generator.generate_reply(email['id'])
                        if result['success']:
                            st.success("Reply draft generated! Check Drafts tab.")
                            st.rerun()
                        else:
                            st.error(f"Error: {result.get('error')}")
            
            with col2:
                if st.button("📝 Summarize", use_container_width=True):
                    with st.spinner("Summarizing..."):
                        result = chat_agent.summarize_email(email['id'])
                        if result['success']:
                            st.info(result['summary'])
                        else:
                            st.error(f"Error: {result.get('error')}")
            
            with col3:
                if st.button("🔄 Re-categorize", use_container_width=True):
                    with st.spinner("Re-categorizing..."):
                        category = email_processor.categorize_email(email)
                        db.update_email_category(email['id'], category)
                        st.success(f"Re-categorized as: {category}")
                        st.rerun()
        else:
            st.info("Select an email from the list to view details")

# Prompt Manager Tab
with tab3:
    st.header("⚙️ Prompt Manager")
    st.markdown("Manage prompts for email categorization, action extraction, and auto-reply generation.")
    
    prompt_types = {
        'categorization': 'Categorization',
        'action_extraction': 'Action Extraction',
        'auto_reply': 'Auto-Reply'
    }
    
    for prompt_type, display_name in prompt_types.items():
        with st.expander(f"📝 {display_name} Prompt", expanded=True):
            prompts = db.get_prompts(prompt_type)
            
            if prompts:
                current_prompt = prompts[0]  # Get most recent active prompt
                
                st.markdown(f"**Last Updated:** {current_prompt.get('updated_at', 'N/A')}")
                
                prompt_content = st.text_area(
                    f"{display_name} Prompt",
                    value=current_prompt['content'],
                    height=300,
                    key=f"prompt_{prompt_type}"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(f"💾 Save Changes", key=f"save_{prompt_type}"):
                        if db.update_prompt(current_prompt['id'], prompt_content):
                            st.success("Prompt updated successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to update prompt")
                
                with col2:
                    if st.button(f"🔄 Restore Default", key=f"restore_{prompt_type}"):
                        if prompt_manager.restore_default(prompt_type):
                            st.success("Default prompt restored!")
                            st.rerun()
                        else:
                            st.error("Failed to restore default")
                
                # Test prompt
                if st.button(f"🧪 Test Prompt", key=f"test_{prompt_type}"):
                    sample_email = db.get_emails(limit=1)
                    if sample_email:
                        email = sample_email[0]
                        with st.spinner("Testing prompt..."):
                            if prompt_type == 'categorization':
                                category = email_processor.categorize_email(email, prompt_content)
                                st.info(f"Result: **{category}**")
                            elif prompt_type == 'action_extraction':
                                items = email_processor.extract_action_items(email, prompt_content)
                                st.json(items)
                            else:
                                st.info("Test feature for auto-reply coming soon")
            else:
                st.warning("No prompt found. Creating default...")
                if st.button(f"Create Default {display_name} Prompt", key=f"create_{prompt_type}"):
                    prompt_manager.restore_default(prompt_type)
                    st.rerun()

# Email Agent Chat Tab
with tab4:
    st.header("💬 Email Agent Chat")
    st.markdown("Ask questions about your inbox, get summaries, and find urgent emails.")
    
    # Suggested queries
    st.subheader("💡 Suggested Queries")
    suggested_queries = [
        "Show me all urgent emails",
        "What are my pending tasks?",
        "Summarize unread emails",
        "Find meeting requests this week"
    ]
    
    cols = st.columns(4)
    for i, query in enumerate(suggested_queries):
        with cols[i]:
            if st.button(query, key=f"suggest_{i}", use_container_width=True):
                st.session_state.chat_input = query
    
    st.markdown("---")
    
    # Chat interface
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    # Display chat history
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your inbox..."):
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Handle special queries
                if "urgent" in prompt.lower():
                    urgent_emails = chat_agent.find_urgent_emails()
                    if urgent_emails:
                        response = f"Found {len(urgent_emails)} urgent emails:\n\n"
                        for item in urgent_emails[:5]:
                            email = item['email']
                            response += f"- **{email['subject']}** ({item['reason']})\n"
                        st.markdown(response)
                        st.session_state.chat_messages.append({"role": "assistant", "content": response})
                    else:
                        response = "No urgent emails found."
                        st.markdown(response)
                        st.session_state.chat_messages.append({"role": "assistant", "content": response})
                
                elif "task" in prompt.lower() or "action" in prompt.lower():
                    action_items = chat_agent.list_action_items()
                    if action_items:
                        response = f"Found {len(action_items)} pending action items:\n\n"
                        for item in action_items[:10]:
                            ai = item['action_item']
                            priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(ai['priority'], '⚪')
                            response += f"{priority_icon} **{ai['task']}**"
                            if ai['deadline']:
                                response += f" (Deadline: {ai['deadline']})"
                            response += "\n"
                        st.markdown(response)
                        st.session_state.chat_messages.append({"role": "assistant", "content": response})
                    else:
                        response = "No pending action items found."
                        st.markdown(response)
                        st.session_state.chat_messages.append({"role": "assistant", "content": response})
                
                else:
                    # General query
                    result = chat_agent.answer_query(prompt)
                    if result['success']:
                        st.markdown(result['answer'])
                        st.session_state.chat_messages.append({"role": "assistant", "content": result['answer']})
                    else:
                        error_msg = f"Error: {result.get('error', 'Unknown error')}"
                        st.error(error_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_messages = []
        chat_agent.clear_history()
        st.rerun()

# Drafts Tab
with tab5:
    st.header("📝 Drafts")
    st.warning("⚠️ **Important**: Drafts are saved locally and never automatically sent. Review before sending.")
    
    # Create new email button
    if st.button("➕ Create New Email", type="primary"):
        st.session_state.show_new_email_form = True
    
    if st.session_state.get('show_new_email_form', False):
        with st.form("new_email_form"):
            st.subheader("Create New Email")
            recipient = st.text_input("Recipient Email")
            purpose = st.text_area("Purpose/Description")
            key_points = st.text_area("Key Points to Include (optional)")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✨ Generate Draft"):
                    if recipient and purpose:
                        with st.spinner("Generating draft..."):
                            result = draft_generator.generate_new_email(recipient, purpose, key_points)
                            if result['success']:
                                st.success("Draft created! Check drafts list below.")
                                st.session_state.show_new_email_form = False
                                st.rerun()
                            else:
                                st.error(f"Error: {result.get('error')}")
                    else:
                        st.warning("Please fill in recipient and purpose")
            
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state.show_new_email_form = False
                    st.rerun()
    
    st.markdown("---")
    
    # List drafts
    drafts = db.get_drafts()
    
    if not drafts:
        st.info("No drafts yet. Create one using 'Create New Email' or generate a reply from an email.")
    else:
        for draft in drafts:
            with st.expander(f"📧 {draft['subject']} - {draft['created_at']}"):
                st.markdown(f"**Subject:** {draft['subject']}")
                st.markdown("**Body:**")
                st.text_area("", draft['body'], height=150, disabled=True, key=f"draft_body_{draft['id']}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("✏️ Edit", key=f"edit_{draft['id']}"):
                        st.session_state[f"editing_{draft['id']}"] = True
                
                with col2:
                    if st.button("🔄 Refine", key=f"refine_{draft['id']}"):
                        refinement = st.text_input("Refinement instructions", key=f"refine_input_{draft['id']}")
                        if refinement:
                            with st.spinner("Refining draft..."):
                                result = draft_generator.refine_draft(draft['id'], refinement)
                                if result['success']:
                                    st.success("Draft refined!")
                                    st.rerun()
                                else:
                                    st.error(f"Error: {result.get('error')}")
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_{draft['id']}"):
                        if db.delete_draft(draft['id']):
                            st.success("Draft deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete draft")
                
                # Edit mode
                if st.session_state.get(f"editing_{draft['id']}", False):
                    new_subject = st.text_input("Subject", value=draft['subject'], key=f"edit_subject_{draft['id']}")
                    new_body = st.text_area("Body", value=draft['body'], height=200, key=f"edit_body_{draft['id']}")
                    
                    if st.button("💾 Save", key=f"save_edit_{draft['id']}"):
                        if db.update_draft(draft['id'], new_subject, new_body):
                            st.success("Draft updated!")
                            st.session_state[f"editing_{draft['id']}"] = False
                            st.rerun()
                        else:
                            st.error("Failed to update draft")
                    
                    if st.button("❌ Cancel", key=f"cancel_edit_{draft['id']}"):
                        st.session_state[f"editing_{draft['id']}"] = False
                        st.rerun()


