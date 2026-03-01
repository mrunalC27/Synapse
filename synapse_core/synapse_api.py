from fastapi import FastAPI
from pydantic import BaseModel
from langchain_groq import ChatGroq
import os

from dotenv import load_dotenv
load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")
app = FastAPI()

summaries = []

groq_api_key = os.getenv("GROQ_API_KEY")

summarizer_llm = ChatGroq(
    model_name="llama-3.1-8b-instant",
    temperature=0.5,
    groq_api_key=groq_api_key
)

class EmailData(BaseModel):
    subject: str
    sender: str
    body: str
    link: str


@app.get("/")
def home():
    return {"status": "Synapse Gmail API Running"}


@app.post("/synapse/gmail")
def receive_email(email: EmailData):

    prompt = f"""
    Summarize this email clearly and briefly:

    Subject: {email.subject}
    From: {email.sender}
    Body: {email.body}
    """

    summary = summarizer_llm.invoke(prompt).content

    summaries.append({
        "subject": email.subject,
        "sender": email.sender,
        "summary": summary,
        "link": email.link
    })

    return {"status": "received"}