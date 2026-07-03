import json
import os
import time
from datetime import datetime, timezone

from fastapi import FastAPI
from pydantic import BaseModel
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv(override=True)

groq_api_key = os.getenv("GROQ_API_KEY")

app = FastAPI(title="Synapse Gmail Brain")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
GMAIL_STORE_PATH = os.path.join(DATA_DIR, "gmail_summaries.json")

summarizer_llm = ChatGroq(
    model_name="llama-3.1-8b-instant",
    temperature=0.3,
    groq_api_key=groq_api_key,
)


def load_store():
    if not os.path.exists(GMAIL_STORE_PATH):
        return []
    try:
        with open(GMAIL_STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_store(store):
    with open(GMAIL_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)


class GmailEvent(BaseModel):
    message_id: str
    thread_id: str
    subject: str
    sender: str
    body: str
    link: str


def summarize_email(subject: str, sender: str, body: str, max_retries: int = 3):
    """Returns the summary text, or None if every retry attempt failed
    (e.g. persistent rate limiting). Callers must check for None and must
    never write None/error text into a real draft."""
    prompt = f"""Summarize this email in 2-3 short sentences. Plain text, no markdown.

Subject: {subject}
From: {sender}
Body: {body[:4000]}
"""
    delay = 2
    for attempt in range(max_retries):
        try:
            return summarizer_llm.invoke(prompt).content.strip()
        except Exception as e:
            is_rate_limit = "rate_limit" in str(e).lower() or "429" in str(e)
            if is_rate_limit and attempt < max_retries - 1:
                print(f"[Gmail] rate limited, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
                delay *= 2
                continue
            print(f"[Gmail] summarization failed permanently: {e}")
            return None
    return None

def draft_reply(subject: str, sender: str, body: str, max_retries: int = 3):
    prompt = f"""Write a short, professional draft reply to this email in 2-3 sentences.
Be polite and address the sender's main point. Plain text only, no markdown, no subject line.
Do not include any preamble like 'Here is a draft reply' - just write the reply itself.

Subject: {subject}
From: {sender}
Body: {body[:4000]}
"""
    delay = 2
    for attempt in range(max_retries):
        try:
            return summarizer_llm.invoke(prompt).content.strip()
        except Exception as e:
            is_rate_limit = "rate_limit" in str(e).lower() or "429" in str(e)
            if is_rate_limit and attempt < max_retries - 1:
                print(f"[Gmail] rate limited on draft_reply, retrying in {delay}s")
                time.sleep(delay)
                delay *= 2
                continue
            print(f"[Gmail] draft_reply failed permanently: {e}")
            return None
    return None

@app.post("/gmail")
def receive_email(data: GmailEvent):
    store = load_store()

    if any(r["message_id"] == data.message_id for r in store):
        return {"status": "duplicate_skipped"}

    summary = summarize_email(data.subject, data.sender, data.body)

    if summary is None:
        return {"status": "failed", "reason": "summarization_unavailable"}

    draft = draft_reply(data.subject, data.sender, data.body)
    # draft can be None if rate limited — n8n's IF node will catch this
    # and skip draft creation, so we still store the summary card regardless.

    record = {
        "message_id": data.message_id,
        "thread_id": data.thread_id,
        "subject": data.subject,
        "sender": data.sender,
        "summary": summary,
        "link": data.link,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    store.append(record)
    save_store(store)

    draft = draft_reply(data.subject, data.sender, data.body)

    return {
        "status": "processed",
        "summary": summary,
        "draft": draft,
    }


@app.get("/gmail")
def get_emails():
    return load_store()[::-1]