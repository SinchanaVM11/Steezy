from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.feedback import FeedbackAction


class AnalysisStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisJobCreate(BaseModel):
    asset_id: UUID


class AnalysisResult(BaseModel):
    category: str
    colors: list[str]
    unknown_attributes: list[str]
    provider: str


class AnalysisJobResponse(BaseModel):
    job_id: UUID
    asset_id: UUID
    user_id: UUID
    status: AnalysisStatus
    result: AnalysisResult | None
    error_code: str | None = Field(default=None)
