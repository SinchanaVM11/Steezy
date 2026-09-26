from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class StoredAsset:
    asset_id: UUID
    user_id: UUID
    content_type: str
    size_bytes: int
    original_filename: str
    storage_key: str
