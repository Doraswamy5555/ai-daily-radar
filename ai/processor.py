"""Rule-based processing for AI Daily Radar items.

This module intentionally uses transparent keyword rules instead of an AI
service. The rules can later be replaced or supplemented by an LLM.
"""

from typing import Any


CATEGORY_KEYWORDS = {
    "models": ("model", "llm", "gpt", "gemini", "claude", "foundation model"),
    "tools": ("tool", "copilot", "agent", "api", "platform", "assistant"),
    "research": ("research", "study", "paper", "benchmark", "dataset", "arxiv"),
    "funding": ("funding", "fundraise", "investment", "raises", "raised", "series a", "series b"),
    "companies": ("company", "startup", "acquisition", "partnership", "acquires"),
}

CATEGORY_EXPLANATIONS = {
    "models": "It may change the AI capabilities available to builders and users.",
    "tools": "It may give teams a new way to use AI in their work.",
    "research": "It may influence how future AI systems are developed or evaluated.",
    "funding": "It signals where investors see momentum in the AI market.",
    "companies": "It may affect the companies shaping the AI ecosystem.",
    "other": "It is a recent development worth tracking in the AI landscape.",
}

TRUSTED_SOURCES = {"TechCrunch AI", "MIT Technology Review AI", "VentureBeat AI"}
HIGH_IMPACT_KEYWORDS = ("launch", "launches", "released", "release", "breakthrough", "new model")


def process_item(item: dict[str, Any]) -> dict[str, Any]:
    """Turn one raw RSS item into a structured AI Radar item."""
    title = item.get("title", "") or ""
    summary = item.get("summary", "") or ""
    source = item.get("source", "") or ""
    category = classify_category(title, summary)

    return {
        "title": title,
        "url": item.get("url", "") or "",
        "published_at": item.get("published_at", "") or "",
        "source": source,
        "summary": summary,
        "category": category,
        "relevance_score": calculate_relevance_score(title, summary, source, category),
        "why_it_matters": build_why_it_matters(category),
    }


def classify_category(title: str, summary: str) -> str:
    """Choose the first matching category using title and summary keywords."""
    text = f"{title} {summary}".lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category

    return "other"


def calculate_relevance_score(
    title: str, summary: str, source: str, category: str
) -> int:
    """Score an item from 1 to 10 using clear, deterministic rules.

    Every item starts at 3. A trusted source, a non-empty summary, a category
    match, and high-impact language each add one point. Funding adds an extra
    point because it often indicates notable market movement.
    """
    score = 3
    text = f"{title} {summary}".lower()

    if source in TRUSTED_SOURCES:
        score += 1
    if summary.strip():
        score += 1
    if category != "other":
        score += 1
    if any(keyword in text for keyword in HIGH_IMPACT_KEYWORDS):
        score += 1
    if category == "funding":
        score += 1

    return max(1, min(score, 10))


def build_why_it_matters(category: str) -> str:
    """Return a short, consistent explanation for a category."""
    return CATEGORY_EXPLANATIONS[category]
