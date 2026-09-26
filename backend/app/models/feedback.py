from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Feedback:
    id: UUID
    user_id: UUID
    wardrobe_item_id: UUID
    action: str
    context: str | None
    created_at: datetime
