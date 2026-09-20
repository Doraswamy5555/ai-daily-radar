"""Small data model used by the SQLite storage layer.

This is a standard-library dataclass, not an ORM model.
"""

from dataclasses import asdict, dataclass


@dataclass
class RadarItem:
    title: str
    url: str
    published_at: str
    source: str
    summary: str
    category: str
    relevance_score: int
    why_it_matters: str
    created_at: str = ""
    id: int | None = None

    def to_dict(self) -> dict[str, object]:
        """Return the item in a JSON-friendly dictionary format."""
        return asdict(self)
