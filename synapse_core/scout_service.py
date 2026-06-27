import json
import os
import re
from langchain_groq import ChatGroq
# import json
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
load_dotenv(override=True)

tavily_api_key = os.getenv("TAVILY_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")


summarizer_llm = ChatGroq(
    model_name="llama-3.1-8b-instant",
    temperature=0.7,
    groq_api_key=groq_api_key
)

def extract_json(text: str):
    """
    Extract JSON array safely from LLM output.
    Removes markdown fences and extra text.
    """

    # remove ```json blocks
    text = re.sub(r"```json|```", "", text)

    # find first JSON array
    match = re.search(r"\[.*\]", text, re.DOTALL)

    if match:
        return json.loads(match.group(0))

    return []


def search_internet(query: str):
    search = TavilySearch(
        tavily_api_key=tavily_api_key,
        max_results=3
    )
    return search.invoke(query)


def run_scout():
    """Generate structured daily briefing with links."""

    topics = {
        "AI & Tech News": "latest AI technology news today",
        "Hackathons": "upcoming hackathons for students 2026",
        "Scholarships": "technology scholarships for students 2026",
        "Tools & Releases": "new developer tools and AI releases"
    }

    briefing_data = {}

    for section, query in topics.items():
        result = search_internet(query)

        prompt = f"""
        Extract 3-5 important items.

        Return ONLY valid JSON.

        Rules:
        - NO HTML
        - NO markdown
        - NO styling
        - Plain text only
        - summary must be 2 concise sentences
        - include real source link

        Format EXACTLY:

        [
        {{
            "title": "string",
            "summary": "plain text summary",
            "link": "https://example.com"
        }}
        ]

        DATA:
        {result}
        """

        response = summarizer_llm.invoke(prompt).content

        try:
            briefing_data[section] = extract_json(response)
        except Exception as e:
            print("Scout parse error:", e)
            briefing_data[section] = []

    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(ROOT_DIR, "data")
    os.makedirs(DATA_DIR, exist_ok=True)
    FILE_PATH = os.path.join(DATA_DIR, "daily_briefing.json")

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(briefing_data, f, indent=2)

    return "Scout briefing generated."


