import pytest

from ai.processor import process_item


@pytest.mark.parametrize(
    ("text", "expected_category"),
    [
        ("A new GPT model", "models"),
        ("A coding copilot tool", "tools"),
        ("A research paper with a new benchmark", "research"),
        ("AI startup raises Series A funding", "funding"),
        ("Company announces an acquisition", "companies"),
        ("This is a general update", "other"),
    ],
)
def test_process_item_classifies_categories(text, expected_category):
    result = process_item({"title": text, "url": "https://example.com", "summary": ""})

    assert result["category"] == expected_category


def test_process_item_calculates_transparent_relevance_score():
    result = process_item(
        {
            "title": "New AI model launches",
            "url": "https://example.com/model",
            "published_at": "2026-01-01",
            "source": "TechCrunch AI",
            "summary": "A new release for developers.",
        }
    )

    assert result["relevance_score"] == 7


def test_process_item_builds_why_it_matters_from_category():
    result = process_item(
        {"title": "AI startup raises funding", "url": "https://example.com/funding"}
    )

    assert result["why_it_matters"] == "It signals where investors see momentum in the AI market."


def test_process_item_handles_a_missing_summary():
    result = process_item({"title": "General AI update", "url": "https://example.com/update"})

    assert result["summary"] == ""
    assert result["category"] == "other"
    assert result["relevance_score"] == 3
