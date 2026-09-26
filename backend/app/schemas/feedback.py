from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FeedbackAction(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    SAVE = "save"
    SKIP = "skip"
    WEAR = "wear"
    NOT_RELEVANT = "not_relevant"


class FeedbackCreate(BaseModel):
    user_id: UUID
    wardrobe_item_id: UUID
    action: FeedbackAction
    context: str | None = Field(default=None, max_length=120)


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    wardrobe_item_id: UUID
    action: FeedbackAction
    context: str | None
    created_at: datetime
