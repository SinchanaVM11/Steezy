from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset_id: UUID
    user_id: UUID
    content_type: str
    size_bytes: int
    original_filename: str
    storage_key: str
