from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class StoredEmbedding:
    wardrobe_item_id: UUID
    user_id: UUID
    values: tuple[float, ...]
    model_name: str
    model_version: str
    dimension: int
    source: str
    created_at: datetime
