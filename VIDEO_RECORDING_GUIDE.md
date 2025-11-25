# Video Recording Guide - Email Productivity Agent

## 🎬 Video Structure (Recommended: 8-10 minutes)

### **Introduction (30 seconds)**
- Brief overview: "This is an Email Productivity Agent built with Streamlit and Google Gemini AI"
- Key features: "It categorizes emails, extracts action items, generates replies, and provides a chat interface"

---

## **Part 1: Dashboard Tab (1-2 minutes)**

### What to Show:
1. **Initial State**
   - Point out: "We start with 20 sample emails loaded from mock inbox"
   - Show the statistics: Total emails, Pending actions, Drafts
   - Show the category breakdown (pie chart) - initially empty/uncategorized

2. **Process Inbox**
   - Click "🔄 Process Inbox" button
   - Show the spinner/loading state
   - Wait for processing to complete
   - **Highlight**: "The AI is categorizing all emails and extracting action items"

3. **Results**
   - Show updated statistics
   - Show the pie chart with categories now populated
   - Point out: "Emails are now categorized into Important, To-Do, Meeting Request, etc."

**Talking Points:**
- "The system uses Google Gemini AI to intelligently categorize emails"
- "It automatically extracts actionable tasks with deadlines and priorities"
- "All processing happens locally in SQLite database"

---

## **Part 2: Inbox Tab (2-3 minutes)**

### What to Show:
1. **Email List**
   - Show the list of emails on the left
   - Point out: "Each email shows sender, subject, and category badge"
   - Show different category colors/icons

2. **Search & Filter**
   - Demonstrate search: Type "meeting" or "urgent"
   - Show filter by category: Select "Important" or "To-Do"
   - Show results updating

3. **View Email Details**
   - Select an email from the list
   - Show full email content on the right
   - Point out: Category badge, timestamp, sender

4. **Action Items**
   - Expand "Action Items" section
   - Show extracted tasks with priorities (🔴 high, 🟡 medium, 🟢 low)
   - Show deadlines if present

5. **Email Actions**
   - Click "✉️ Generate Reply" - show draft generation
   - Click "📝 Summarize" - show AI summary
   - Click "🔄 Re-categorize" - show re-categorization

**Talking Points:**
- "The inbox provides a clean interface to browse and search emails"
- "Action items are automatically extracted with priorities"
- "You can generate professional replies with one click"

---

## **Part 3: Prompt Manager Tab (1-2 minutes)**

### What to Show:
1. **View Default Prompts**
   - Expand each prompt type (Categorization, Action Extraction, Auto-Reply)
   - Show the default prompt content
   - Explain: "These prompts control how the AI processes emails"

2. **Edit a Prompt**
   - Edit the Categorization prompt (add a small change)
   - Click "💾 Save Changes"
   - Show success message

3. **Test Prompt**
   - Click "🧪 Test Prompt" on Categorization
   - Show the test result on a sample email
   - Point out: "You can test prompts before saving"

4. **Restore Default**
   - Click "🔄 Restore Default"
   - Show prompt restored

**Talking Points:**
- "Prompts are customizable - you can fine-tune how the AI works"
- "Test feature lets you see results before committing changes"
- "All prompts are stored in the database with version history"

---

## **Part 4: Email Agent Chat Tab (2 minutes)**

### What to Show:
1. **Suggested Queries**
   - Point out the 4 suggested query buttons
   - Click "Show me all urgent emails"
   - Show the response with urgent emails listed

2. **Custom Query**
   - Type in chat: "What are my pending tasks?"
   - Show the AI response with action items
   - Show conversation history

3. **Another Query**
   - Type: "Find meeting requests this week"
   - Show intelligent response

4. **Clear Chat**
   - Click "🗑️ Clear Chat"
   - Show history cleared

**Talking Points:**
- "Natural language interface to query your inbox"
- "The AI understands context and provides relevant answers"
- "Conversation history is maintained for context"

---

## **Part 5: Drafts Tab (1-2 minutes)**

### What to Show:
1. **View Generated Drafts**
   - Show drafts from earlier "Generate Reply" action
   - Expand a draft to show full content
   - Point out: Subject and body

2. **Edit Draft**
   - Click "✏️ Edit" on a draft
   - Show edit form with subject and body
   - Make a small edit
   - Click "💾 Save"
   - Show updated draft

3. **Refine Draft**
   - Click "🔄 Refine" on a draft
   - Enter: "Make it more formal and add a call to action"
   - Show AI refining the draft
   - Show updated content

4. **Create New Email**
   - Click "➕ Create New Email"
   - Fill in form:
     - Recipient: "client@example.com"
     - Purpose: "Follow up on project proposal"
     - Key Points: "Thank them for meeting, provide timeline, ask for feedback"
   - Click "✨ Generate Draft"
   - Show generated draft

5. **Delete Draft**
   - Click "🗑️ Delete" on a draft
   - Show confirmation and deletion

**Talking Points:**
- "All drafts are saved locally - never automatically sent"
- "AI can refine drafts based on your instructions"
- "Create professional emails from scratch with just a purpose"

---

## **Part 6: Live Email Demo (Optional - 2 minutes)**

### Add a New Email Manually:
1. Go to Inbox tab
2. Explain: "Let me show you how it processes a new email"
3. Use one of the sample emails below (copy-paste)
4. Process it and show categorization and action extraction

---

## **Conclusion (30 seconds)**
- Summarize key features
- Mention: "Built with Streamlit, Google Gemini AI, and SQLite"
- Highlight: "All processing is local, drafts never auto-send"
- Call to action: "Check the README for setup instructions"

---

## 📧 Sample Emails for Live Demo

### Email 1: Urgent Meeting Request
```
From: sarah.johnson@company.com
Subject: URGENT: Board Meeting Tomorrow at 3 PM
Body:
Hi,

We need to reschedule the board meeting to tomorrow (Wednesday) at 3 PM IST. This is urgent as we need to discuss the Q4 results before the deadline.

Please confirm your availability ASAP. The meeting will be in Conference Room A.

Thanks,
Sarah Johnson
CEO
```

### Email 2: Project Update with Action Items
```
From: tech.team@startup.io
Subject: Sprint 15 Status Update - Action Required
Body:
Hello Team,

Here's our sprint 15 status:

✅ Completed:
- User authentication module
- Payment gateway integration
- API documentation

🔄 In Progress:
- Frontend dashboard
- Unit tests

⏳ Blocked:
- Need approval for database migration (by Friday)
- Waiting on design assets from design team

Action Items:
1. Review and approve database migration plan by Friday EOD
2. Provide feedback on API documentation by Thursday
3. Schedule demo for stakeholders next week

Let me know if you have any questions.

Best,
Tech Team Lead
```

### Email 3: Newsletter
```
From: newsletter@techweekly.com
Subject: Weekly Tech Digest - AI & ML Updates
Body:
Hello Tech Enthusiast!

This week's top stories:

🤖 AI News:
- OpenAI releases GPT-5 beta
- Google announces new Gemini features
- Latest research from NeurIPS 2024

💻 Development:
- New VS Code extensions
- Python 3.13 released
- Docker best practices

Read more: www.techweekly.com

Unsubscribe | Manage Preferences
```

### Email 4: Client Request with Deadline
```
From: client@business.com
Subject: Project Deliverable Review - Deadline: Jan 25
Body:
Hi,

I need you to review the project deliverables document and provide feedback by January 25th. This is high priority as we have a client presentation on January 28th.

Please focus on:
- Technical feasibility
- Timeline accuracy
- Resource requirements
- Risk assessment

The document is attached. Let me know if you need any clarification.

Thanks,
Client Manager
```

### Email 5: Spam-like Email
```
From: security@bank-verify.com
Subject: URGENT: Verify Your Account Now!
Body:
Dear Customer,

We detected suspicious activity on your account. Click here immediately to verify: http://suspicious-link.com/verify

Your account will be suspended in 24 hours if you don't act now.

This is an automated message. Do not reply.
```

---

## 🎯 Key Points to Emphasize

1. **AI-Powered**: "Uses Google Gemini AI for intelligent processing"
2. **Local & Private**: "All data stored locally in SQLite, never sent to external servers"
3. **Safety First**: "Drafts are never automatically sent - always requires manual review"
4. **Customizable**: "Prompts can be edited to fine-tune AI behavior"
5. **User-Friendly**: "Clean UI with search, filters, and visualizations"
6. **Comprehensive**: "Categorization, action extraction, chat interface, and draft generation"

---

## 📝 Video Recording Tips

1. **Screen Recording Settings**:
   - Record at 1080p or higher
   - Show cursor movements clearly
   - Use zoom for important details

2. **Audio**:
   - Speak clearly and at moderate pace
   - Explain what you're doing as you do it
   - Pause briefly after key actions

3. **Timing**:
   - Don't rush through features
   - Show loading states (they're quick but visible)
   - Wait for AI responses to complete

4. **Highlights**:
   - Zoom in on category badges and action items
   - Show the pie chart clearly
   - Highlight AI-generated content (drafts, summaries)

5. **Common Mistakes to Avoid**:
   - Don't skip the "Process Inbox" step
   - Don't forget to show error handling (if any errors occur)
   - Don't rush through the Prompt Manager

---

## 🔄 Recommended Video Flow

```
1. Introduction (30s)
   ↓
2. Dashboard - Show stats → Process Inbox → Show results (2min)
   ↓
3. Inbox - Browse → Search → View email → Show action items → Generate reply (3min)
   ↓
4. Prompt Manager - View prompts → Edit → Test → Restore (2min)
   ↓
5. Chat Agent - Suggested queries → Custom query → Show responses (2min)
   ↓
6. Drafts - View drafts → Edit → Refine → Create new email (2min)
   ↓
7. Conclusion (30s)
```

**Total: ~12 minutes** (can be edited down to 8-10 minutes)

---

## 💡 Pro Tips for Recording

- **Before Recording**: 
  - Clear browser cache
  - Restart the app fresh
  - Have sample emails ready to copy-paste

- **During Recording**:
  - Use keyboard shortcuts (Ctrl+F for search, etc.)
  - Speak naturally as if explaining to a friend
  - Show enthusiasm for the features

- **After Recording**:
  - Add text overlays for key features
  - Add background music (optional, keep it subtle)
  - Add transitions between sections

Good luck with your video! 🎥✨

