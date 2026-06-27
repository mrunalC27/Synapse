from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import requests
from apscheduler.schedulers.background import BackgroundScheduler 
from datetime import datetime 
import pytz
# (we will call your Groq model from here later)
# from synapse_core.scout_service import run_scout
from scout_service import run_scout

app = FastAPI(title="Synapse Gmail Brain")
scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

def scheduled_scout(): 
    print("Running scheduled Scout:", datetime.now()) 
    run_scout()

scheduler.add_job( 
    scheduled_scout, 
    trigger="cron", 
    hour=7,
    minute=0

    #for testing every minute, use:
    # minute="*/1"
)

@app.on_event("startup") 
def start_scheduler(): 
    scheduler.start() 
    print("Scout scheduler started.")


gmail_store = []


class GmailEvent(BaseModel):
    subject: str
    sender: str
    body: str
    link: str


# TEMP summary function (replace with LLM next step)
def summarize_email(subject, body):
    short = body[:300]
    return f"Summary of '{subject}':\n{short}..."


@app.post("/gmail")
def receive_email(data: GmailEvent):

    summary = summarize_email(data.subject, data.body)

    record = {
        "subject": data.subject,
        "sender": data.sender,
        "summary": summary,
        "link": data.link,
        "timestamp": datetime.utcnow().isoformat(),
    }

    gmail_store.append(record)

    return {"status": "processed"}


@app.get("/gmail")
def get_emails():
    return gmail_store[::-1]