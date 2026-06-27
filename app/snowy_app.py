
import sys
import os 
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)
import streamlit as st
from synapse_core.synapse_api import summaries
from synapse_core.scout_service import run_scout
import streamlit.components.v1 as components
import textwrap
import re
import gc
import hashlib
import uuid
import streamlit as st
# import os
import io
from contextlib import redirect_stdout
import json
import shutil
import dateparser
import tempfile
import requests
from dateutil import parser
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

from langchain_huggingface import HuggingFaceEmbeddings
# from langchain.embeddings import HuggingFaceEmbeddings
# from langchain_chroma import Chroma
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_tavily import TavilySearch

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from dotenv import load_dotenv
# import os

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")



from datetime import datetime, timedelta, timezone
DB_PERSIST_DIRECTORY = "chroma_db_unified"

#file kuthun run hoat ahe check karaych asel tr
#print("Running from:", os.getcwd())

# ----------------- PAGE CONFIG ----------------- #
st.set_page_config(page_title="Synapse Agent", page_icon="🧠", layout="wide")

# ----------------- GLOBAL CSS ----------------- #
st.markdown("""

<style>
@import url('https://fonts.googleapis.com/icon?family=Material+Icons');

@import url('https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&display=swap');

html, body, [class*="css"] {
    background-color: #000000 !important;
    color: #e0e0e0 !important;
    font-family: 'Montserrat', sans-serif !important;
}
.stApp {
    background-color: #000000 !important;
}

/* Hide default streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }

/* Dashboard title */
.synapse-title {
    font-family: 'Syne', sans-serif;
    font-size: 3rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.02em;
    line-height: 1;
    margin-bottom: 0.25rem;
}

.synapse-subtitle {
    font-family: 'DM Sans', sans-serif;
    font-size: 1rem;
    font-weight: 300;
    color: #555;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 3rem;
}

/* Cards */
.synapse-card {
    background: #0a0a0a;
    border: 1px solid #007474;
    border-radius: 12px;
    padding: 1.75rem 1.5rem 1.5rem 1.5rem;
    margin-bottom: 1.25rem;
    position: relative;
    overflow: hidden;
    transition: all 0.25s ease;
    box-shadow: 0 0 0px #007474;
    cursor: pointer;
    min-height: 180px;
}

.synapse-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #007474, transparent);
    opacity: 0.8;
}

.synapse-card:hover {
    border-color: #00b3b3;
    box-shadow: 0 0 24px rgba(0, 116, 116, 0.35), inset 0 0 30px rgba(0, 116, 116, 0.04);
    transform: translateY(-2px);
}

.card-icon {
    font-size: 2rem;
    margin-bottom: 0.75rem;
    display: block;
}

.card-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.4rem;
    letter-spacing: 0.01em;
}

.card-desc {
    font-size: 1.0rem;
    color: #666;
    line-height: 1.5;
    margin-bottom: 1.2rem;
    font-weight: 300;
}

/* Neon button */
.stButton > button {
    width: auto !important;
    min-width: 120px !important;   /* adjust this */
    padding: 0.4rem 1rem !important;
    justify-content: center !important;
            
    background: transparent !important;
    border: 1px solid #007474 !important;
    color: #007474 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 0.4rem 1.2rem !important;
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    background: #007474 !important;
    color: #000 !important;
    box-shadow: 0 0 14px rgba(0, 116, 116, 0.5) !important;
}

/* Back button */
.back-btn > button {
    border-color: #333 !important;
    color: #555 !important;
    font-size: 0.72rem !important;
}

.back-btn > button:hover {
    background: #111 !important;
    color: #fff !important;
    box-shadow: none !important;
}

/* Module header */
.module-header {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.25rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.module-divider {
    height: 1px;
    background: linear-gradient(90deg, #007474, transparent);
    margin-bottom: 1.5rem;
    opacity: 0.5;
}

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    background: #0d0d0d !important;
    border: 1px solid #1a1a1a !important;
    border-radius: 6px !important;
    color: #e0e0e0 !important;
    font-family: 'DM Sans', sans-serif !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #007474 !important;
    box-shadow: 0 0 0 1px #007474 !important;
}
            
      
/* Target the tabs' labels */
div[data-testid="stHorizontalBlock"] > div > button {
    font-size: 20px !important;  /* Increase font size */
    font-weight: 600 !important; /* Make it bolder */
    padding: 10px 20px !important;
}

/* Chat messages */
.stChatMessage {
    background: #0a0a0a !important;
    border: 1px solid #111 !important;
    border-radius: 8px !important;
}

/* Sidebar */
.css-1d391kg, [data-testid="stSidebar"] {
    background-color: #050505 !important;
    border-right: 1px solid #0d0d0d !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: #0a0a0a !important;
    border: 1px dashed #007474 !important;
    border-radius: 8px !important;
}

/* Spinner */
.stSpinner > div {
    border-top-color: #007474 !important;
}

/* Success / error messages */
.stSuccess { background: #001a1a !important; border-color: #007474 !important; }
.stError   { background: #1a0000 !important; }

/* Divider */
hr { border-color: #111 !important; }
</style>
""", unsafe_allow_html=True)

# ----------------- CONSTANTS ----------------- #
TASKS_FILE = "tasks.txt"
DB_PERSIST_DIRECTORY = "chroma_db"
SCOPES = ["https://www.googleapis.com/auth/calendar"]
MAX_MESSAGES = 8

API_KEY = groq_api_key
TAVILY_API_KEY = tavily_api_key

# ----------------- SESSION STATE INIT ----------------- #
if "active_module" not in st.session_state:
    st.session_state.active_module = None
if "messages" not in st.session_state:
    st.session_state.messages = [AIMessage(content="Hello! I'm Synapse. How can I help you today?")]
if "last_processed_file" not in st.session_state:
    st.session_state.last_processed_file = None


# ----------------- GOOGLE AUTH HELPERS ----------------- #
def get_credentials():
    creds = None
    if os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        except Exception:
            creds = None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError("credentials.json not found.")
            
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(
                port=0,
                access_type='offline',   # 🔥 ADD THIS
                prompt='consent'         # 🔥 ADD THIS
            )

            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

def clean_time_phrase(text: str) -> str:
    if not text:
        return text
    fillers = ["to", "on", "from", "move", "shift", "reschedule", "at", "update", "change"]
    words = text.lower().split()
    cleaned = [w for w in words if w not in fillers]
    return " ".join(cleaned)

def extract_time(text: str):
    return dateparser.parse(text, settings={"RETURN_AS_TIMEZONE_AWARE": False}, languages=["en"])

def extract_date(text: str, base):
    return dateparser.parse(
        text,
        settings={"RELATIVE_BASE": base, "PREFER_DATES_FROM": "future",
                  "RETURN_AS_TIMEZONE_AWARE": True, "TIMEZONE": "Asia/Kolkata"},
        languages=["en"]
    )

def sanitize_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("'", "").replace('"', '').replace("\n", " ")
    return text.strip()

def find_event_by_summary_on_date(summary: str, date_str: str):
    try:
        creds = get_credentials()
        service = build("calendar", "v3", credentials=creds)
        start_of_day = f"{date_str}T00:00:00+05:30"
        end_of_day = f"{date_str}T23:59:59+05:30"
        events_result = service.events().list(
            calendarId="primary", timeMin=start_of_day, timeMax=end_of_day,
            singleEvents=True, orderBy="startTime"
        ).execute()
        for event in events_result.get("items", []):
            if summary.lower() in event.get("summary", "").lower():
                return event
        return None
    except Exception:
        return None

def fetch_gmail():
    try:
        r = requests.get("http://127.0.0.1:9000/gmail", timeout=2)
        return r.json()
    except:
        return []
        
# ----------------- TOOLS ----------------- #
@tool
def add_task(task_description: str) -> str:
    """Add a task to the task list."""
    try:
        with open(TASKS_FILE, "a") as f:
            f.write(task_description + "\n")
        return f"Successfully added task: '{task_description}'"
    except Exception as e:
        return f"Error adding task: {e}"

@tool
def list_tasks() -> str:
    """List all your current tasks."""
    if not os.path.exists(TASKS_FILE):
        return "You have no tasks saved yet."
    try:
        with open(TASKS_FILE, "r") as f:
            tasks = f.readlines()
        if not tasks:
            return "Your task list is empty."
        return "Here are your tasks:\n" + "\n".join(
            [f"{i+1}. {t.strip()}" for i, t in enumerate(tasks)]
        )
    except Exception as e:
        return f"Error reading tasks: {e}"

@tool
def delete_todo_task(task_number: int) -> str:
    """Delete a task by its number."""
    if not os.path.exists(TASKS_FILE):
        return "No tasks found."
    with open(TASKS_FILE, "r") as f:
        tasks = f.readlines()
    if task_number < 1 or task_number > len(tasks):
        return "Invalid task number."
    deleted_task = tasks.pop(task_number - 1)
    with open(TASKS_FILE, "w") as f:
        f.writelines(tasks)
    return f"Deleted task: '{deleted_task.strip()}'"

# @tool
# def search_knowledge_base(query: str) -> str:
#     """Search the uploaded documents (knowledge base)."""
#     if not os.path.exists(DB_PERSIST_DIRECTORY):
#         return "The knowledge base is empty. Please upload a document first."
#     try:
#         embeddings = st.session_state.embeddings
#         vector_store = Chroma(persist_directory=DB_PERSIST_DIRECTORY, embedding_function=embeddings)
#         retriever = vector_store.as_retriever(search_kwargs={"k": 3})
#         relevant_docs = retriever.invoke(query)
#         if not relevant_docs:
#             return "No relevant info found."
#         return "\n---\n".join([doc.page_content for doc in relevant_docs])
#     except Exception as e:
#         return f"Error searching docs: {e}"
# @tool
# def search_knowledge_base(query: str) -> str:
#     """Search the uploaded documents (knowledge base)."""
#     if not os.path.exists(DB_PERSIST_DIRECTORY):
#         return "The knowledge base is empty. Please upload a document first."
#     try:
#         embeddings = st.session_state.embeddings
#         if "vector_store" in st.session_state:
#             vector_store = st.session_state.vector_store
#         else:
#             vector_store = Chroma(persist_directory=DB_PERSIST_DIRECTORY, embedding_function=embeddings)
#             st.session_state.vector_store = vector_store
#         retriever = vector_store.as_retriever(search_kwargs={"k": 3})
#         relevant_docs = retriever.invoke(query)
#         if not relevant_docs:
#             return "No relevant info found."
#         return "\n---\n".join([doc.page_content for doc in relevant_docs])
#     except Exception as e:
#         return f"Error searching docs: {e}"
@tool
def search_knowledge_base(query: str) -> str:
    """Search the uploaded documents (knowledge base)."""
    try:
        if "vector_store" in st.session_state:
            vector_store = st.session_state.vector_store
        elif os.path.exists(DB_PERSIST_DIRECTORY):
            vector_store = Chroma(
                persist_directory=DB_PERSIST_DIRECTORY,
                embedding_function=st.session_state.embeddings
            )
            st.session_state.vector_store = vector_store
        else:
            return "The knowledge base is empty. Please upload a document first."

        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        # relevant_docs = retriever.get_relevant_documents(query)  # <-- use get_relevant_documents
        relevant_docs = retriever.invoke(query)
        if not relevant_docs:
            return "No relevant info found."
        return "\n---\n".join([doc.page_content for doc in relevant_docs])
    except Exception as e:
        return f"Error searching docs: {e}"


#OG TOOL
# @tool
# def get_daily_briefing() -> str:
#     """Return text from daily_briefing.txt if present."""
#     if not os.path.exists("daily_briefing.txt"):
#         return "No briefing found. The scout hasn't run yet."
#     try:
#         with open("daily_briefing.txt", "r", encoding="utf-8") as f:
#             return f.read()
#     except Exception as e:
#         return f"Error reading briefing: {e}"

@tool
def get_daily_briefing():
    """Return the structured daily scout briefing."""
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FILE_PATH = os.path.join(BASE_DIR, "data", "daily_briefing.json")

    if not os.path.exists(FILE_PATH):
        return {}
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    FILE_PATH = os.path.join(BASE_DIR, "data", "daily_briefing.json")

    if not os.path.exists(FILE_PATH):
        return {}

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
# def run_scout():
#     """Collect tech updates and create daily briefing."""

#     topics = [
#         "latest AI news today",
#         "upcoming hackathons for students",
#         "technology scholarships 2026",
#         "new developer tools released",
#     ]

#     collected_text = ""

#     for topic in topics:
#         search_result = search_internet.invoke({"query": topic})
#         collected_text += f"\n\n=== {topic.upper()} ===\n{search_result}"

#     summarize_prompt = f"""
#     Create a clean daily tech briefing from the following information.

#     Organize into sections:
#     - AI & Tech News
#     - Hackathons
#     - Scholarships
#     - Tools & Releases

#     Keep concise and readable.

#     DATA:
#     {collected_text}
#     """

#     briefing = summarizer_llm.invoke(summarize_prompt).content

#     with open("daily_briefing.txt", "w", encoding="utf-8") as f:
#         f.write(briefing)

#     return "Daily briefing generated successfully."

def extract_json(text: str):
    """Extract JSON array from LLM output safely."""
    
    # remove markdown fences
    text = re.sub(r"```json|```", "", text)

    # find first JSON array
    match = re.search(r"\[.*\]", text, re.DOTALL)

    if match:
        return json.loads(match.group(0))

    return []



@tool
def list_calendar_events() -> str:
    """List the next 10 upcoming events from primary Google Calendar."""
    try:
        creds = get_credentials()
        service = build("calendar", "v3", credentials=creds)

        now = datetime.utcnow().isoformat() + "Z"
        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])

        if not events:
            return "No upcoming events found."

        event_list = []

        for i, event in enumerate(events):
            start_raw = event["start"].get("dateTime", event["start"].get("date"))

            dt = parser.parse(start_raw)
            formatted_time = dt.strftime("%d %b %Y, %I:%M %p")

            summary = event.get("summary", "No title")

            event_list.append(f"{i+1}. {summary} → {formatted_time}")

        return "Upcoming Calendar Events:\n" + "\n".join(event_list)

    except Exception as e:
        return f"Calendar Error: {e}"
# @tool
# def list_calendar_events() -> str:
#     """List the next 10 upcoming events from primary Google Calendar."""
#     try:
#         creds = get_credentials()
#         service = build("calendar", "v3", credentials=creds)
#         now = datetime.utcnow().isoformat() + "Z"
#         events_result = service.events().list(
#             calendarId="primary", timeMin=now, maxResults=10,
#             singleEvents=True, orderBy="startTime"
#         ).execute()
#         events = events_result.get("items", [])
#         if not events:
#             return "No upcoming events found."
#         event_list = []
#         for event in events:
#             start = event["start"].get("dateTime", event["start"].get("date"))
#             summary = event.get("summary", "No title")
#             eid = event.get("id")
#             # event_list.append(f"- {start}: {summary} (ID: {eid})")

            

#             event_list = []
#             for i, event in enumerate(events):
#                 start_raw = event["start"].get("dateTime", event["start"].get("date"))
                
#                 dt = parser.parse(start_raw)
#                 formatted_time = dt.strftime("%d %b %Y, %I:%M %p")  # 🔥 readable format

#                 summary = event.get("summary", "No title")
#                 eid = event.get("id")

#                 event_list.append(f"{i+1}. {summary} → {formatted_time}")
                
#         return "Upcoming Calendar Events:\n" + "\n".join(event_list)
#     except Exception as e:
#         return f"Calendar Error: {e}"

@tool
def add_calendar_event(summary: str, start_time: str = None, end_time: str = None, description: str = "") -> str:
    """Add a new event to Google Calendar using natural-language date/time."""
    try:
        creds = get_credentials()
        service = build("calendar", "v3", credentials=creds)
        tz = timezone(timedelta(hours=5, minutes=30))
        base = datetime.now(tz)
        if not start_time:
            start_dt = base.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            start_dt = dateparser.parse(
                start_time,
                settings={"RELATIVE_BASE": base, "PREFER_DATES_FROM": "future",
                          "RETURN_AS_TIMEZONE_AWARE": True, "TIMEZONE": "Asia/Kolkata"},
                languages=["en"]
            )
            if not start_dt:
                return "Could not understand the start date/time."
        if not end_time:
            end_dt = start_dt + timedelta(hours=1)
        else:
            end_dt = dateparser.parse(
                end_time,
                settings={"RELATIVE_BASE": start_dt, "PREFER_DATES_FROM": "future",
                          "RETURN_AS_TIMEZONE_AWARE": True, "TIMEZONE": "Asia/Kolkata"},
                languages=["en"]
            )
            if not end_dt:
                return "Could not understand the end date/time."

        start_of_day = start_dt.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        end_of_day = start_dt.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()
        events_result = service.events().list(
            calendarId="primary", timeMin=start_of_day, timeMax=end_of_day,
            singleEvents=True, orderBy="startTime"
        ).execute()
        for event in events_result.get("items", []):
            evt_start = event["start"].get("dateTime")
            if not evt_start:
                continue
            evt_start_parsed = dateparser.parse(evt_start, settings={"RETURN_AS_TIMEZONE_AWARE": True})
            if abs((evt_start_parsed - start_dt).total_seconds()) < 60 and \
               event.get("summary", "").lower() == summary.lower():
                return "⚠️ Event already exists at this exact time."

        event_body = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
        }
        created_event = service.events().insert(calendarId="primary", body=event_body).execute()
        st.session_state.last_deleted_or_added = {"action": "add", "event": created_event}
        return f"Event '{summary}' created! Link: {created_event.get('htmlLink')}"
    except Exception as e:
        return f"Error adding event: {e}"

@tool
def update_calendar_event_by_natural_language(
    summary: str, new_time_nl: str = None, old_time_nl: str = None, description: str = ""
):
    """Update a Google Calendar event using natural language."""
    try:
        creds = get_credentials()
        service = build("calendar", "v3", credentials=creds)
        tz = timezone(timedelta(hours=5, minutes=30))
        base = datetime.now(tz)
        old_start = None

        if new_time_nl:
            cleaned = clean_time_phrase(new_time_nl)
            time_part = extract_time(cleaned)
            date_part = extract_date(cleaned, base)
            if not date_part and old_start:
                date_part = old_start
            if not time_part:
                return "Could not understand the new time."
            new_start = date_part.replace(hour=time_part.hour, minute=time_part.minute,
                                          second=0, microsecond=0)
        else:
            new_start = base.replace(hour=0, minute=0, second=0, microsecond=0)
        new_end = new_start + timedelta(hours=1)

        now_iso = datetime.utcnow().isoformat() + "Z"
        events_result = service.events().list(
            calendarId="primary", q=summary, timeMin=now_iso,
            singleEvents=True, orderBy="startTime"
        ).execute()
        events = [e for e in events_result.get("items", [])
                  if e.get("summary", "").lower() == summary.lower()]
        if not events:
            return f"No upcoming event found with title '{summary}'."

        found_event = None
        if old_time_nl:
            cleaned_old_time = clean_time_phrase(old_time_nl)
            old_start = dateparser.parse(
                cleaned_old_time,
                settings={"RELATIVE_BASE": base, "RETURN_AS_TIMEZONE_AWARE": True,
                          "TIMEZONE": "Asia/Kolkata"},
                languages=["en"]
            )
            if old_start:
                for event in events:
                    evt_start = event["start"].get("dateTime")
                    if not evt_start:
                        continue
                    evt_start_parsed = dateparser.parse(
                        evt_start, settings={"RETURN_AS_TIMEZONE_AWARE": True}, languages=["en"]
                    )
                    if abs((evt_start_parsed - old_start).total_seconds()) < 3600:
                        found_event = event
                        break
        if not found_event:
            found_event = events[0]

        found_event["start"]["dateTime"] = new_start.isoformat()
        found_event["end"]["dateTime"] = new_end.isoformat()
        if description:
            found_event["description"] = description

        updated = service.events().update(
            calendarId="primary", eventId=found_event["id"], body=found_event
        ).execute()
        st.session_state.last_deleted_or_added = {"action": "update", "event": updated}
        return f"Event updated: {updated.get('htmlLink')}"
    except Exception as e:
        return f"Error updating event: {e}"

@tool
def delete_calendar_event(summary: str, event_date_nl: str) -> str:
    """Delete an event by its summary and a natural-language date."""
    try:
        dt = dateparser.parse(event_date_nl, settings={"RETURN_AS_TIMEZONE_AWARE": True})
        if not dt:
            return "Could not parse the date."
        date_str = dt.strftime("%Y-%m-%d")
        event = find_event_by_summary_on_date(summary, date_str)
        if not event:
            return f"No event found matching '{summary}' on {date_str}."
        creds = get_credentials()
        service = build("calendar", "v3", credentials=creds)
        st.session_state.last_deleted_or_added = {"action": "delete", "event": event}
        service.events().delete(calendarId="primary", eventId=event["id"]).execute()
        return f"Event '{summary}' on {date_str} deleted."
    except Exception as e:
        return f"Error deleting event: {e}"
    
@tool
def undo_last_action() -> str:
    """Undo the last calendar action (add or delete)."""
    if "last_deleted_or_added" not in st.session_state:
        return "No recent action to undo."
    last_action = st.session_state.last_deleted_or_added
    event = last_action["event"]
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)
    try:
        if last_action["action"] == "delete":
            clean_event = {
                "summary": event.get("summary"),
                "description": event.get("description", ""),
                "start": event.get("start"),
                "end": event.get("end"),
                "location": event.get("location", ""),
                "attendees": event.get("attendees", [])
            }
            restored = service.events().insert(calendarId="primary", body=clean_event).execute()
            st.session_state.last_deleted_or_added = None
            return f"Deleted event restored: {restored.get('summary')}"
        elif last_action["action"] == "add":
            service.events().delete(calendarId="primary", eventId=event["id"]).execute()
            st.session_state.last_deleted_or_added = None
            return f"Last added event '{event.get('summary')}' removed."
        else:
            return "Nothing to undo."
    except Exception as e:
        return f"Error undoing last action: {e}"

@tool
def search_internet(query: str) -> str:
    """Search the live internet for real-time information using Tavily."""
    if isinstance(query, dict):
        query = query.get("query") or query.get("input") or ""
    query = str(query).strip()
    if not query:
        return "No query provided."
    try:
        search = TavilySearch(tavily_api_key=tavily_api_key, max_results=3)
        result = search.invoke(query)
        if isinstance(result, dict) and "results" in result:
            output = []
            for r in result.get("results", []):
                title = r.get("title", "No title")
                url = r.get("url", "")
                content = r.get("content", "")
                output.append(f"{title}\n{url}\n{content}")
            return "\n---\n".join(output) if output else "No results found."
        elif isinstance(result, str):
            return result
        return "No results returned from Tavily."
    except Exception as e:
        return f"Tavily search error: {e}"

# ----------------- LLM / EMBEDDINGS SETUP ----------------- #
@st.cache_resource
def load_models():
    try:
        agent_llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0, groq_api_key=groq_api_key)
        summarizer_llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.7, groq_api_key=groq_api_key)
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        return agent_llm, summarizer_llm, embeddings
    except Exception as e:
        st.error(f"Error loading models: {e}")
        return None, None, None

llm, summarizer_llm, embeddings = load_models()

TOOLS = [
    add_task, list_tasks, delete_todo_task, search_knowledge_base, search_internet,
    list_calendar_events, get_daily_briefing,
    add_calendar_event, update_calendar_event_by_natural_language,
    delete_calendar_event, undo_last_action
]

TOOL_MAP = {
    "add_task": add_task, "list_tasks": list_tasks, "delete_todo_task": delete_todo_task,
    "search_knowledge_base": search_knowledge_base, "search_internet": search_internet,
    "list_calendar_events": list_calendar_events, "get_daily_briefing": get_daily_briefing,
    "add_calendar_event": add_calendar_event,
    "update_calendar_event_by_natural_language": update_calendar_event_by_natural_language,
    "delete_calendar_event": delete_calendar_event, "undo_last_action": undo_last_action
}

SYSTEM_PROMPT = SystemMessage(content="""
You are a helpful AI assistant called Synapse.

Rules:
- If the user greets (hello, hi, hey), respond politely.
- If the user asks general knowledge or definitions, answer directly.
- You have access to a search_internet tool.
- When you need to look something up, provide arguments in valid JSON format.
- ONLY call tools when real-time, personal, or external data is required.
""")

if llm and summarizer_llm and embeddings:
    st.session_state.embeddings = embeddings
    llm_with_tools = llm.bind_tools(TOOLS)
else:
    st.error("Failed to load AI models. Please check your API key.")
    st.stop()

# ----------------- MODULE RENDER FUNCTIONS ----------------- #

def render_back_button():
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)
    if st.button("← Back to Dashboard"):
        st.session_state.active_module = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def render_module_header(icon: str, title: str):
    st.markdown(f'<div class="module-header">{icon} {title}</div>', unsafe_allow_html=True)
    st.markdown('<div class="module-divider"></div>', unsafe_allow_html=True)

def module_chat():
    # render_module_header("", "Chat")
    render_module_header(
    '<span class="material-icons" style="margin-top: 3px;font-size:35px;color:#FFFFFFF;">chat_bubble</span>',
    "Chat"
    )
    render_back_button()

    for msg in st.session_state.messages:
        if isinstance(msg, ToolMessage):
            continue
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        avatar = "👤" if role == "user" else "🤖"
        with st.chat_message(role, avatar=avatar):
            st.markdown(msg.content)

    if user_prompt := st.chat_input("Ask Synapse anything..."):
        st.session_state.messages.append(HumanMessage(content=user_prompt))
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_prompt)
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                messages_to_send = [SYSTEM_PROMPT] + st.session_state.messages[-MAX_MESSAGES:]
                response = llm_with_tools.invoke(messages_to_send)
                if response.tool_calls:
                    tool_call = response.tool_calls[0]
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_to_call = TOOL_MAP.get(tool_name)
                    if tool_to_call:
                        tool_output = tool_to_call.invoke(tool_args) if isinstance(tool_args, dict) \
                            else tool_to_call.invoke({"input": tool_args})
                    else:
                        tool_output = f"Error: Tool '{tool_name}' not found."
                    st.session_state.messages.append(
                        ToolMessage(content=tool_output, tool_call_id=tool_call["id"])
                    )
                    if tool_name in ["search_internet", "search_knowledge_base", "list_calendar_events"]:
                        summarize_prompt = (
                            f'User question: "{user_prompt}"\nTool result: "{tool_output}"\n'
                            f"Answer clearly using the tool result."
                        )
                        final_response = summarizer_llm.invoke(summarize_prompt).content
                    else:
                        final_response = tool_output
                else:
                    final_response = response.content
                st.markdown(final_response)
                st.session_state.messages.append(AIMessage(content=final_response))

def module_tasks():
    render_module_header('<span class="material-icons" style="margin-top: 3px;font-size:35px;color:#FFFFFFF;">assignment_turned_in</span>', "Tasks")
    render_back_button()

    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Add a task")
        new_task = st.text_input("abcd", placeholder="e.g. Review quarterly report", label_visibility="collapsed")
    with col2:
        st.write("")
        st.write("")
        st.write("")  
        st.write("")
        if st.button("Add Task", use_container_width=True):
            if new_task.strip():
                result = add_task.invoke({"task_description": new_task.strip()})
                st.success(result)
            else:
                st.warning("Please enter a task description.")

    st.divider()
    st.subheader("Current Tasks")
    if st.button("🔄 Refresh Task List"):
        st.rerun()

    tasks_output = list_tasks.invoke({})
    st.markdown(f"```\n{tasks_output}\n```")

    st.divider()
    st.subheader("Delete a Task")

    task_num = st.number_input("Enter task number to delete", min_value=1, step=1, value=1)
    if st.button("Delete Task", use_container_width=False):
        # Get latest tasks
        tasks_output = list_tasks.invoke({})
       # Count tasks (assuming each task is on a new line and starts with number)
        task_lines = [
            line for line in tasks_output.split("\n")
            if re.match(r"^\d+\.", line.strip())
        ]

        total_tasks = len(task_lines)

        if task_num > total_tasks:
            st.error(f"Task {task_num} does not exist. You only have {total_tasks} task(s).")
        else:
            result = delete_todo_task.invoke({"task_number": int(task_num)})
            st.info(result)
            st.rerun()

def module_calendar():
    render_module_header('<span class="material-icons" style="margin-top: 3px;font-size:35px;color:#FFFFFFF;">calendar_month</span>', "Calendar")
    render_back_button()

    tab1, tab2, tab3, tab4 = st.tabs(["📋 View Events", "➕ Add Event", "✏️ Update Event", "🗑️ Delete Event"])

    with tab1:
        if st.button("Fetch Upcoming Events"):
            with st.spinner("Loading calendar..."):
                creds = get_credentials()
                service = build("calendar", "v3", credentials=creds)

                now = datetime.utcnow().isoformat() + "Z"
                events_result = service.events().list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=10,
                    singleEvents=True,
                    orderBy="startTime"
                ).execute()

                events = events_result.get("items", [])
                st.session_state.events = events  # ✅ STORE HERE

                # display nicely
                if not events:
                    st.info("No upcoming events")
                else:
                    for i, event in enumerate(events):
                        start_raw = event["start"].get("dateTime", event["start"].get("date"))
                        dt = parser.parse(start_raw)
                        formatted = dt.strftime("%d %b %Y, %I:%M %p")
                        st.write(f"{i+1}. {event.get('summary')} → {formatted}")
        

    with tab2:
        summary = st.text_input("Event title", placeholder="e.g. Team standup",)

        start_time = st.text_input("Start time", placeholder="e.g. tomorrow 3pm",)
       
        end_time = st.text_input("End time", placeholder="e.g. tomorrow 4pm",)
   
        description = st.text_area("Description (optional)",)

        if st.button("Add Event", key="add_cal"):
            # Check if required fields are filled
            if not summary.strip() or not start_time.strip() or not end_time.strip():
                st.error("Please fill in all required fields")
            else:
                with st.spinner("Adding event..."):
                    result = add_calendar_event.invoke({
                    "summary": summary, "start_time": start_time,
                    "end_time": end_time, "description": description
                })
                st.success(result)
  

    # with tab3:
    #     summary_u = st.text_input("Event title to update", placeholder="e.g. Team standup")
    #     new_time = st.text_input("New time", placeholder="e.g. next Monday 5pm")
    #     old_time = st.text_input("Current time (optional)", placeholder="e.g. tomorrow 3pm")
    #     if st.button("Update Event", key="update_cal"):
    #         with st.spinner("Updating event..."):
    #             result = update_calendar_event_by_natural_language.invoke({
    #                 "summary": summary_u, "new_time_nl": new_time, "old_time_nl": old_time
    #             })
    #             st.success(result)

    with tab3:
        # st.subheader("Update Event")

        events = st.session_state.get("events", [])

        if not events:
            st.warning("⚠️ First fetch events from 'View Events' tab")
        else:
            # Create dropdown options
            event_options = []
            for event in events:
                start_raw = event["start"].get("dateTime", event["start"].get("date"))
                dt = parser.parse(start_raw)
                formatted = dt.strftime("%d %b %Y, %I:%M %p")
                title = event.get("summary", "No title")

                event_options.append(f"{title} → {formatted}")

            selected_index = st.selectbox(
                "Select event to update",
                range(len(event_options)),
                format_func=lambda x: event_options[x]
            )

            new_time = st.text_input(
                "New time",
                placeholder="e.g. tomorrow 5pm"
            )

            if st.button("Update Event", key="update_cal"):
                if not new_time.strip():
                    st.error("Please enter new time")
                else:
                    try:
                        creds = get_credentials()
                        service = build("calendar", "v3", credentials=creds)

                        selected_event = events[selected_index]
                        event_id = selected_event["id"]

                        tz = timezone(timedelta(hours=5, minutes=30))
                        base = datetime.now(tz)

                        new_start = dateparser.parse(
                            new_time,
                            settings={
                                "RELATIVE_BASE": base,
                                "PREFER_DATES_FROM": "future",
                                "RETURN_AS_TIMEZONE_AWARE": True,
                                "TIMEZONE": "Asia/Kolkata"
                            },
                            languages=["en"]
                        )

                        if not new_start:
                            st.error("Could not understand the new time.")
                        else:
                            new_end = new_start + timedelta(hours=1)

                            selected_event["start"]["dateTime"] = new_start.isoformat()
                            selected_event["end"]["dateTime"] = new_end.isoformat()

                            updated = service.events().update(
                                calendarId="primary",
                                eventId=event_id,
                                body=selected_event
                            ).execute()

                            st.success(f"✅ Event updated: {updated.get('summary')}")

                    except Exception as e:
                        st.error(f"Error: {e}")


    # with tab4:
    #     summary_d = st.text_input("Event title to delete", placeholder="e.g. Team standup")
    #     date_nl = st.text_input("Event date", placeholder="e.g. tomorrow")
    #     if st.button("Delete Event", key="delete_cal"):
    #         with st.spinner("Deleting..."):
    #             result = delete_calendar_event.invoke({
    #                 "summary": summary_d, "event_date_nl": date_nl
    #             })
    #             st.warning(result)


    with tab4:
        st.subheader("Delete Event")

        events = st.session_state.get("events", [])

        if not events:
            st.warning("⚠️ First fetch events from 'View Events' tab")
        else:
            event_options = []
            for event in events:
                start_raw = event["start"].get("dateTime", event["start"].get("date"))
                dt = parser.parse(start_raw)
                formatted = dt.strftime("%d %b %Y, %I:%M %p")
                title = event.get("summary", "No title")

                event_options.append(f"{title} → {formatted}")

            selected_index = st.selectbox(
                "Select event to delete",
                range(len(event_options)),
                format_func=lambda x: event_options[x],
                key="delete_select"
            )

            if st.button("Delete Event", key="delete_cal"):
                try:
                    creds = get_credentials()
                    service = build("calendar", "v3", credentials=creds)

                    selected_event = events[selected_index]
                    event_id = selected_event["id"]

                    # ✅ Store for undo
                    st.session_state.last_deleted_or_added = {
                        "action": "delete",
                        "event": selected_event
                    }

                    service.events().delete(
                        calendarId="primary",
                        eventId=event_id
                    ).execute()

                    st.success(f"🗑️ Event deleted: {selected_event.get('summary')}")

                    st.session_state.events.pop(selected_index)

                except Exception as e:
                    st.error(f"Error deleting event: {e}")

        # ✅ Undo button (IMPORTANT)
        if "last_deleted_or_added" in st.session_state and st.session_state.last_deleted_or_added:
            if st.button("↩️ Undo Last Delete"):
                result = undo_last_action.invoke({})
                st.info(result)

# def module_gmail_whatsapp():
#     render_module_header("📨", "Gmail & WhatsApp")
#     render_back_button()
#     st.info("🚧 Gmail & WhatsApp integration coming soon. Connect your accounts to send messages, read emails, and automate communication directly from Synapse.")
#     st.markdown("""
# **Planned features:**
# - Read & summarize Gmail inbox
# - Compose and send emails via AI
# - Send WhatsApp messages via Twilio/WhatsApp API
# - Smart reply suggestions
#     """)


def module_gmail_whatsapp():
    render_module_header("📨", "Gmail Automation")
    render_back_button()
    
    st.info("📬 Gmail summaries will appear below as they arrive:")

    # Display email summaries live (newest first)
    # if summaries:
    #     for email in summaries[::-1]:
    #         st.subheader(email['subject'])
    #         st.write(f"From: {email['sender']}")
    #         st.write(email['summary'])
    #         st.markdown(f"[Open in Gmail]({email['link']})")
    # else:
    #     st.write("No email summaries yet.")

 
    # emails = fetch_gmail()

    # if emails:
    #     for email in emails:
    #         st.subheader(email["subject"])
    #         st.write(f"From: {email['sender']}")
    #         st.write(email["summary"])
    #         st.markdown(f"[Open in Gmail]({email['link']})")
    # else:
    #     st.write("No email summaries yet.")
    emails = fetch_gmail()

    if emails:
        for email in emails:
            st.markdown(f"""
            <div class="synapse-card">
                <div class="card-title">📨 {email["subject"]}</div>
                <div class="card-desc"><b>From:</b> {email["sender"]}</div>
                <div style="margin-top:10px; color:#ccc;">
                    {email["summary"]}
                </div>
                <div style="margin-top:12px;">
                    <a href="{email['link']}" target="_blank"
                    style="
                        text-decoration:none;
                        border:1px solid #007474;
                        padding:6px 12px;
                        border-radius:8px;
                        color:#007474;
                        font-size:12px;
                        letter-spacing:0.05em;">
                    OPEN IN GMAIL →
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.write("No email summaries yet.")
        

def module_scout():
    render_module_header("🔭", "Scout — Daily Briefing")
    render_back_button()

    col1, col2 = st.columns(2)
    # with col1:
    #     st.subheader("Today's Briefing")
    #     if st.button("📰 Load Daily Briefing"):
    #         with st.spinner("Fetching briefing..."):
    #             result = get_daily_briefing.invoke({})
    #             st.text_area("Briefing", result, height=300)
    with col1:
        st.subheader("Today's Briefing")

        if st.button("🚀 Run Scout Now"):
            with st.spinner("Scout collecting updates..."):
                run_scout()
                st.success("Briefing generated!")

        briefing = get_daily_briefing.invoke({})

        if briefing:
            for section, items in briefing.items():

                st.markdown(f"### {section}")

                for item in items:
                   components.html(f"""
                    <style>
                    body {{
                        margin:0;
                        background:#000;
                        font-family:Montserrat, sans-serif;
                    }}

                    .synapse-card {{
                        background:#0a0a0a;
                        border:1px solid #007474;
                        border-radius:12px;
                        padding:18px;
                        margin-bottom:10px;
                    }}

                    .card-title {{
                        font-size:18px;
                        font-weight:700;
                        color:white;
                        margin-bottom:6px;
                    }}

                    .summary {{
                        color:#cccccc;
                        font-size:14px;
                        line-height:1.5;
                    }}

                    .open-btn {{
                        text-decoration:none;
                        border:1px solid #007474;
                        padding:6px 12px;
                        border-radius:8px;
                        color:#00b3b3;
                        font-size:12px;
                        display:inline-block;
                        margin-top:12px;
                    }}
                    </style>

                    <div class="synapse-card">
                        <div class="card-title">{item['title']}</div>

                        <div class="summary">
                            {item['summary']}
                        </div>

                        <a class="open-btn" href="{item['link']}" target="_blank">
                            OPEN RESOURCE →
                        </a>
                    </div>
                    
                    """, height=160)
        else:
            st.info("No briefing generated yet.")

    with col2:
        st.subheader("Internet Search")
        query = st.text_input("Search the web", placeholder="e.g. latest AI news today")
        if st.button("🔍 Search"):
            with st.spinner("Searching..."):
                result = search_internet.invoke({"query": query})
                summarize_prompt = (
                    f'User query: "{query}"\nSearch result: "{result}"\n'
                    f"Summarize clearly and concisely."
                )
                summary = summarizer_llm.invoke(summarize_prompt).content
                st.markdown(summary)

def module_pdf():
    render_module_header('<span class="material-icons" style="margin-top: 3px;font-size:35px;color:#FFFFFFF;">edit_document</span>', "Document Analyzer")
    render_back_button()
    if "indexed_hashes" not in st.session_state:
        st.session_state.indexed_hashes = set()

    if "indexed_files" not in st.session_state:
        st.session_state.indexed_files = []
    
    # with st.sidebar:
    st.subheader("Upload PDF")
    # uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", key="pdf_uploader")

    uploaded_files = st.file_uploader(
    "Choose PDF files",
    type="pdf",
    accept_multiple_files=True,
    key="pdf_uploader"
    )


    if "last_processed_file" not in st.session_state:
        st.session_state.last_processed_file = None

    if "embeddings" not in st.session_state:
        st.session_state.embeddings = embeddings  # embeddings from your LLM setup
    # if "indexed_files" not in st.session_state:
    #     st.session_state.indexed_files = set()
    
    # if uploaded_file and uploaded_file.name != st.session_state.last_processed_file:
    if st.button("📥 Process Uploaded PDFs"):
        if uploaded_files:
            for uploaded_file in uploaded_files:

                # if uploaded_file.name in st.session_state.indexed_files:
                #     st.info(f"📄 {uploaded_file.name} already indexed. Skipping.")
                #     continue
                # ✅ Create file hash
                file_bytes = uploaded_file.getvalue()
                file_hash = hashlib.md5(file_bytes).hexdigest()

                # ✅ Duplicate check
                # if file_hash in st.session_state.indexed_files:
                if file_hash in st.session_state.indexed_hashes:
                    st.info(f"📄 {uploaded_file.name} already indexed. Skipping.")
                    continue

                with st.spinner("Processing PDF..."):
                    try:
                        temp_file_path = os.path.join(".", uploaded_file.name)
                        with open(temp_file_path, "wb") as f_out:
                            f_out.write(uploaded_file.getbuffer())
                        loader = PyPDFLoader(temp_file_path)
                        documents = loader.load()
                        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                        chunks = text_splitter.split_documents(documents)
                        if not chunks:
                            raise Exception("No text found in PDF.")
                    # if os.path.exists(DB_PERSIST_DIRECTORY):
                    #     shutil.rmtree(DB_PERSIST_DIRECTORY)

                    # if "vector_store" in st.session_state:
                    #     st.session_state.vector_store = None

                    # gc.collect()

                    # if os.path.exists(DB_PERSIST_DIRECTORY):
                    #     shutil.rmtree(DB_PERSIST_DIRECTORY)

                    # vector_store = Chroma.from_documents(
                    #     chunks,
                    #     st.session_state.embeddings,  # use session state embeddings
                    #     persist_directory=DB_PERSIST_DIRECTORY
                    # )
                    # ✅ Create unique folder for this upload

                    #Version 1
                    # unique_id = str(uuid.uuid4())
                    # persist_path = os.path.join("chroma_db", unique_id)

                    # vector_store = Chroma.from_documents(
                    #     chunks,
                    #     st.session_state.embeddings,
                    #     persist_directory=persist_path
                    # )
                    # Add metadata (important!)
                        for chunk in chunks:
                            chunk.metadata["source"] = uploaded_file.name

                        # If DB exists → load and append
                        if os.path.exists(DB_PERSIST_DIRECTORY):
                            vector_store = Chroma(
                                persist_directory=DB_PERSIST_DIRECTORY,
                                embedding_function=st.session_state.embeddings
                            )
                            vector_store.add_documents(chunks)

                        # If DB does not exist → create new
                        else:
                            vector_store = Chroma.from_documents(
                                chunks,
                                st.session_state.embeddings,
                                persist_directory=DB_PERSIST_DIRECTORY
                            )

                        vector_store.persist()
                        st.session_state.vector_store = vector_store



                        # Store in session
                        # st.session_state.vector_store = vector_store
                        # st.session_state.current_db_path = persist_path


                        # vector_store.persist()  # save to disk
                        # st.session_state.vector_store = vector_store  # keep in session

                        os.remove(temp_file_path)
                        st.success(f"✅ PDF '{uploaded_file.name}' processed and indexed!")
                        # st.session_state.indexed_files.add(file_hash)
                        st.session_state.indexed_hashes.add(file_hash)
                        st.session_state.indexed_files.append(uploaded_file.name)

                        st.session_state.last_processed_file = uploaded_file.name
                    except Exception as e:
                        st.error(f"Error processing PDF: {e}")


    if st.session_state.indexed_files:
        st.markdown("### 📚 Indexed Documents")
        for file in st.session_state.indexed_files:
            st.write(f"- {file}")

    st.subheader("Search Your Document")
    pdf_query = st.text_input("Ask a question about your PDF", placeholder="e.g. What are the key findings?")



    # if st.button("🔍 Search Knowledge Base"):
    #     if not os.path.exists(DB_PERSIST_DIRECTORY):
    #         st.warning("Please upload a PDF first.")
        
    #     else:
    #         with st.spinner("Searching..."):
    #             raw = search_knowledge_base.invoke({"query": pdf_query})
    #             summarize_prompt = (
    #                 f'User query: "{pdf_query}"\nDocument excerpts: "{raw}"\n'
    #                 f"Answer the question based on the document content."
    #             )
    #             answer = summarizer_llm.invoke(summarize_prompt).content
    #             st.markdown("**Answer:**")
    #             st.markdown(answer)
    #             with st.expander("Raw excerpts"):
    #                 st.text(raw)

    if st.button("🔍 Search Knowledge Base"):
        if not st.session_state.indexed_files:
            st.warning("Please upload at least one PDF first.")
        if not os.path.exists(DB_PERSIST_DIRECTORY):
            st.warning("Please upload at least one PDF first.")
        else:
            with st.spinner("Searching..."):
                vector_store = Chroma(
                    persist_directory=DB_PERSIST_DIRECTORY,
                    embedding_function=st.session_state.embeddings
                )

                retriever = vector_store.as_retriever(search_kwargs={"k": 4})
                docs = retriever.invoke(pdf_query)

                raw = "\n\n".join(
                    [f"(Source: {doc.metadata.get('source','Unknown')})\n{doc.page_content}"
                    for doc in docs]
                )

                summarize_prompt = (
                    f'User query: "{pdf_query}"\n\n'
                    f'Document excerpts:\n{raw}\n\n'
                    f"Answer ONLY using the provided excerpts."
                )

                answer = summarizer_llm.invoke(summarize_prompt).content

                st.markdown("**Answer:**")
                st.markdown(answer)

                with st.expander("Raw excerpts"):
                    st.text(raw)


# ----------------- CARD DEFINITIONS ----------------- #
CARDS = [
    {
        "id": "chat",
        "icon": '<span class="material-icons" style="margin-top: 10px;font-size:35px;color:#FFFFFFF;">chat_bubble</span>',
        "title": "Chat",
        "desc": "Conversational AI with tool access. Ask anything, get answers powered by real-time search and your data.",
        "render": module_chat,
    },
    {
        "id": "tasks",
        "icon": '<span class="material-icons" style="margin-top: 10px;font-size:35px;color:#FFFFFFF;">assignment_turned_in</span>',
        "title": "Tasks",
        "desc": "Add, view, and delete your to-do items. Stay organized with a persistent task list.",
        "render": module_tasks,
    },
    {
        "id": "calendar",
        "icon": '<span class="material-icons" style="margin-top: 10px;font-size:35px;color:#FFFFFFF;">calendar_month</span>',
        "title": "Calendar",
        "desc": "Manage your Google Calendar. Create, update, or delete events using natural language.",
        "render": module_calendar,
    },
    {
        "id": "gmail_whatsapp",
        "icon": '<span class="material-icons" style="margin-top: 10px;font-size:35px;color:#FFFFFFF;">mail</span>',
        "title": "Gmail Automation",
        "desc": "Automate sending, sorting, and responding to emails with intelligent Gmail workflows.",
        "render": module_gmail_whatsapp,
    },
    {
        "id": "scout",
        "icon": '<span class="material-icons" style="margin-top: 10px;font-size:35px;color:#FFFFFFF;">travel_explore</span>',
        "title": "Scout",
        "desc": "Your daily briefing and live internet search tool. Stay informed with curated insights.",
        "render": module_scout,
    },
    {
        "id": "pdf",
        "icon": '<span class="material-icons" style="margin-top: 10px;font-size:35px;color:#FFFFFFF;">edit_document</span>',
        "title": "Document Analyzer",
        "desc": "Upload any PDF and ask questions. Semantic search extracts precise answers from your documents.",
        "render": module_pdf,
    },
]

# ----------------- DASHBOARD RENDER ----------------- #
def render_dashboard():
    st.markdown('<div class="synapse-title">SYNAPSE</div>', unsafe_allow_html=True)
    st.markdown('<div class="synapse-subtitle">Intelligent Workspace · v10</div>', unsafe_allow_html=True)

    cols_per_row = 3
    for row_start in range(0, len(CARDS), cols_per_row):
        row_cards = CARDS[row_start: row_start + cols_per_row]
        cols = st.columns(cols_per_row, gap="medium")
        for col, card in zip(cols, row_cards):
            with col:
                st.markdown(f"""
                <div class="synapse-card">
                    <span class="card-icon">{card['icon']}</span>
                    <div class="card-title">{card['title']}</div>
                    <div class="card-desc">{card['desc']}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Open {card['title']}", key=f"btn_{card['id']}", use_container_width=True):
                    st.session_state.active_module = card["id"]
                    st.rerun()


# ----------------- ROUTER ----------------- #
active = st.session_state.get("active_module")

if active is None:
    render_dashboard()
else:
    module_fn = next((c["render"] for c in CARDS if c["id"] == active), None)
    if module_fn:
        module_fn()
    else:
        st.error("Module not found.")
        st.session_state.active_module = None
        st.rerun()