from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class WardrobeItem:
    id: UUID
    user_id: UUID
    category: str
    subcategory: str | None
    colors: tuple[str, ...]
    source: str
    verification_status: str
    created_at: datetime
    updated_at: datetime
