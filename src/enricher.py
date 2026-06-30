import os
import re
import time
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq

class CleanedLead(BaseModel):
    clean_company_name: str = Field(description="The formal company name stripped of LLC, Inc, Corp, or regional suffixes.")
    industry: str = Field(description="The primary business category (e.g., SaaS, E-commerce, Real Estate).")
    personalized_icebreaker: str = Field(description="A 1-sentence sales hook combining their title and their company function.")

# Global state for lazy initialization of the LLM client
_structured_llm = None


def reset_llm_cache() -> None:
    global _structured_llm
    _structured_llm = None


def get_llm():
    global _structured_llm
    if _structured_llm is None:
        groq_api_key = os.getenv("GROQ_API_KEY")
        llm = ChatGroq(
            temperature=0.2,
            model_name="qwen/qwen3-32b",
            groq_api_key=groq_api_key
        )
        _structured_llm = llm.with_structured_output(CleanedLead)
    return _structured_llm

def fallback_clean_company(raw_name: str) -> str:
    if not raw_name or raw_name.lower() == "unknown company":
        return "Your Company"
    # Basic regex cleanup of corporate suffixes
    clean = re.sub(r'\b(LLC|Inc|Corp|Ltd|Co|Group|Corporation|Incorporated|Limited)\b\.?', '', raw_name, flags=re.IGNORECASE)
    clean = re.sub(r'[\s,\.-]+$', '', clean)
    return clean.strip() or raw_name

def fallback_icebreaker(name: str, title: str, clean_company: str) -> str:
    return f"Hi {name}, I noticed your work as {title} at {clean_company} and wanted to reach out regarding optimizing your team's workflow."

def process_lead_with_ai(name: str, title: str, raw_company: str, description: str, max_retries: int = 3) -> CleanedLead:
    """
    Sends raw lead data to Groq to extract clean details and generate icebreakers.
    Includes rate-limit retry logic and exponential backoff.
    """
    ai_prompt = (
        f"Lead Name: {name} | Job Title: {title} | "
        f"Raw Company Name: {raw_company} | Description: {description}"
    )
    
    structured_llm = get_llm()
    
    for attempt in range(1, max_retries + 1):
        try:
            analysis = structured_llm.invoke(f"Extract and clean this lead info: {ai_prompt}")
            if analysis and getattr(analysis, "clean_company_name", None):
                return analysis
        except Exception as e:
            print(f"⚠️ Groq LLM attempt {attempt}/{max_retries} failed for '{name}': {e}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)  # Exponential backoff: 2s, 4s, 8s
                
    # Fallback to local python heuristics if all retries fail
    print(f"⚠️ All LLM attempts failed for '{name}'. Using programmatic fallback.")
    clean_company = fallback_clean_company(raw_company)
    icebreaker = fallback_icebreaker(name, title, clean_company)
    return CleanedLead(
        clean_company_name=clean_company,
        industry="B2B Business",
        personalized_icebreaker=icebreaker
    )
