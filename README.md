# Synapse — AI-Powered Personal Workspace
 
Synapse is a modular AI agent built with Streamlit that brings together six intelligent modules into a single personal dashboard. It connects to your Google Calendar, Gmail, and the live web — all running locally on your machine.
 
---
 
## Modules
 
### 🤖 Chat
Conversational AI powered by LLaMA 3.3-70B (via Groq). Supports real-time web search via Tavily, document Q&A via your uploaded PDFs, and calendar/task management — all through natural language.
 
### ✅ Tasks
A persistent to-do list. Add, view, and delete tasks directly or through the Chat module.
 
### 📅 Calendar
Full Google Calendar integration. Create, update, delete, and recover events using plain English — "schedule a meeting tomorrow at 3pm", "move my Monday standup to 5pm". All times displayed in IST.
 
### 📨 Gmail Automation
Automatically fetches unread Gmail messages every 10 minutes via an n8n workflow. For each email:
- Generates a 2-3 sentence AI summary (displayed as a card on the dashboard)
- Generates a professional draft reply, saved directly below the original email in Gmail
- Provides a direct link to open that specific email in Gmail
Powered by a local FastAPI backend (`synapse_core/server.py`) running on port 9000, with Groq LLM summarization, rate-limit retry logic, deduplication by Gmail message ID, and persistent JSON storage.
 
### 🔭 Scout
Daily tech briefing auto-generated every morning at 07:00 IST. Searches the web for:
- Latest AI & tech news
- Upcoming hackathons for students
- Technology scholarships
- New developer tools and releases
Results are displayed as cards on the dashboard. Can also be triggered manually. The dashboard auto-refreshes every 5 minutes to pick up the latest briefing without a page reload.
 
### 📄 Document Analyzer
Upload one or more PDFs and ask questions about them. Uses semantic search (ChromaDB + HuggingFace embeddings) to find relevant passages, then answers using the Groq LLM. Supports multiple documents simultaneously with source attribution.
 
---
 
## Architecture
 
```
Snowy_Synapse/
├── snowy_app.py              # Main Streamlit app (all 6 modules)
├── synapse_core/
│   ├── server.py             # FastAPI Gmail backend (port 9000)
│   └── scout_service.py      # Scout web search + briefing generation
├── data/                     # Runtime data (gitignored)
│   ├── daily_briefing.json   # Scout's latest briefing
│   └── gmail_summaries.json  # Processed Gmail records
├── .env                      # API keys (gitignored)
├── credentials.json          # Google OAuth client (gitignored)
└── token.json                # Google OAuth token (gitignored)
```
 
**Three processes run simultaneously:**
1. `python -m streamlit run snowy_app.py` — the dashboard (default port 8501)
2. `python -m uvicorn synapse_core.server:app --host 127.0.0.1 --port 9000 --reload` — Gmail backend
3. `n8n start` — workflow engine (port 5678) that polls Gmail and feeds the backend
---
 
## Setup
 
### Prerequisites
- Python 3.11+
- Node.js (for n8n)
- A Google Cloud project with Calendar API and Gmail API enabled
### 1. Clone and install
 
```bash
git clone https://github.com/mrunalC27/Synapse.git
cd Synapse
python -m venv venv
venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt
```
 
### 2. Environment variables
 
Create a `.env` file in the project root:
 
```
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```
 
Get your keys from:
- Groq: https://console.groq.com
- Tavily: https://app.tavily.com
### 3. Google OAuth setup
 
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project, enable **Google Calendar API** and **Gmail API**
3. Create an OAuth 2.0 Client ID (Desktop app type) — download as `credentials.json` and place in project root
4. Add your Gmail address as a test user under OAuth consent screen
5. On first run, a browser window will open for Google sign-in — this generates `token.json` automatically
### 4. n8n Gmail workflow setup
 
Install n8n globally:
```bash
npm install -g n8n
```
 
Create a second OAuth Client ID (Web application type) in Google Cloud Console with redirect URI:
```
http://localhost:5678/rest/oauth2-credential/callback
```
 
In n8n (`localhost:5678`), build this workflow:
 
```
Schedule Trigger (every 10 min)
  → Gmail: Get Many Messages (filter: is:unread, limit: 5-10)
  → Wait (2 seconds)
  → HTTP Request POST http://127.0.0.1:9000/gmail
      body: { message_id, thread_id, subject, sender, body (snippet), link }
  → IF: status == "processed" AND draft is not empty
      → Gmail: Create a Draft
          Subject: {{ original subject }}
          Message: {{ $json.draft }}
          Thread ID: {{ original threadId }}
          To Email: {{ original From }}
```
 
Activate the workflow — it will run automatically every 10 minutes while n8n is running.
 
### 5. Run everything
 
Open three terminal windows (all with venv activated):
 
**Terminal 1 — Gmail backend:**
```bash
python -m uvicorn synapse_core.server:app --host 127.0.0.1 --port 9000 --reload
```
 
**Terminal 2 — Dashboard:**
```bash
python -m streamlit run snowy_app.py
```
 
**Terminal 3 — n8n:**
```bash
n8n start
```
 
Open `http://localhost:8501` in your browser.
 
---
 
## API Keys needed
 
| Key | Purpose | Free tier |
|---|---|---|
| Groq | LLM for chat, summarization, draft replies | Yes — 30 RPM on llama-3.1-8b-instant |
| Tavily | Web search for Scout and Chat | Yes — no preset limit |
| Google OAuth | Calendar + Gmail access | Yes |
 
---
 
## Known limitations
 
- All three processes (Streamlit, uvicorn, n8n) must be running simultaneously for full functionality. No persistent background service is set up by default — closing any terminal stops that component.
- Groq's free tier caps at 30 requests per minute. The Gmail workflow uses a Wait node and retry logic to stay within limits, but processing very large backlogs (50+ unread emails) in one run may hit rate limits temporarily.
- Scout's 7 AM auto-briefing only fires if Streamlit is actively running at that time (uses APScheduler inside the Streamlit process). For guaranteed daily runs regardless of whether the app is open, set up a Windows Task Scheduler job pointing to `python -c "from synapse_core.scout_service import run_scout; run_scout()"`.
- The Document Analyzer's ChromaDB vector store (`chroma_db/`) is local only and not committed to git — re-upload your PDFs after a fresh clone.
---
 
## Tech stack
 
| Layer | Technology |
|---|---|
| Frontend/UI | Streamlit |
| LLM | LLaMA 3.3-70B, LLaMA 3.1-8B via Groq |
| Web search | Tavily |
| Gmail automation | n8n + FastAPI |
| Vector search | ChromaDB + HuggingFace all-MiniLM-L6-v2 |
| Google APIs | Google Calendar API, Gmail API |
| Scheduler | APScheduler (in-process) |
| Backend | FastAPI + Uvicorn |
 
---