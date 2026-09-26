from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.wardrobe import WardrobeItemResponse


class SimilaritySearchRequest(BaseModel):
    embedding: list[float] = Field(min_length=1, max_length=4096)
    top_k: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.0, ge=-1, le=1)

    @field_validator("embedding")
    @classmethod
    def finite_embedding(cls, values: list[float]) -> list[float]:
        if not all(value == value and abs(value) != float("inf") for value in values):
            raise ValueError("embedding values must be finite")
        return values


class RetrievalMetadata(BaseModel):
    score: float
    model_name: str
    model_version: str
    dimension: int
    source: str
    created_at: datetime


class SimilaritySearchResult(BaseModel):
    item: WardrobeItemResponse
    retrieval: RetrievalMetadata
    rank: int


class SimilaritySearchResponse(BaseModel):
    semantics: str = "baseline_low_level_visual_similarity"
    query_dimension: int
    results: list[SimilaritySearchResult]
