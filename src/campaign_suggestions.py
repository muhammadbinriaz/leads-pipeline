import os

from langchain_groq import ChatGroq
from pydantic import BaseModel, Field


class TargetingSuggestions(BaseModel):
    job_titles: list[str] = Field(
        description="6-10 decision-maker job titles relevant to the niche, no duplicates."
    )
    outreach_angle: str = Field(
        description="One professional sentence describing the best outreach angle for this campaign."
    )
    recommended_limit: int = Field(
        description="Suggested lead count for a first test run (between 5 and 50).",
        ge=5,
        le=50,
    )


def suggest_campaign_targeting(
    groq_api_key: str,
    industry: str,
    country: str,
    campaign_goal: str = "",
) -> TargetingSuggestions:
    """Generate AI-suggested job titles and outreach angle for a campaign."""
    os.environ["GROQ_API_KEY"] = groq_api_key.strip()

    llm = ChatGroq(
        temperature=0.3,
        model_name="qwen/qwen3-32b",
        groq_api_key=groq_api_key.strip(),
    )
    structured = llm.with_structured_output(TargetingSuggestions)

    prompt = (
        "You are a B2B lead generation strategist. Suggest targeting for a prospecting campaign.\n"
        f"Industry / niche: {industry or 'General B2B'}\n"
        f"Target country: {country}\n"
        f"Campaign goal: {campaign_goal or 'Build a qualified outreach list'}\n"
        "Return practical job titles commonly found in Apollo-style databases."
    )
    result = structured.invoke(prompt)
    if not result or not result.job_titles:
        raise ValueError("AI returned empty suggestions. Try again with more detail in Industry.")
    return result
