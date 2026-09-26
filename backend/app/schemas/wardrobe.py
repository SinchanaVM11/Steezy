from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WardrobeItemCreate(BaseModel):
    user_id: UUID
    category: str = Field(min_length=1, max_length=80)
    subcategory: str | None = Field(default=None, min_length=1, max_length=80)
    colors: list[str] = Field(default_factory=list, max_length=8)
    source: str = Field(default="user", pattern="^(user|imported)$")


class WardrobeItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    category: str
    subcategory: str | None
    colors: list[str]
    source: str
    verification_status: str
    asset_id: UUID | None
    analysis_job_id: UUID | None
    analysis_provider: str | None
    analysis_unknown_attributes: list[str]
    created_at: datetime
    updated_at: datetime
