from pydantic import BaseModel, Field


class Prediction(BaseModel):
    value: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    source: str
    model_name: str | None = None
    model_version: str | None = None


class EmbeddingMetadata(BaseModel):
    model_name: str
    model_version: str
    dimension: int = Field(gt=0)
    source: str


class VisualEmbedding(BaseModel):
    values: list[float]
    metadata: EmbeddingMetadata


class FashionItemRepresentation(BaseModel):
    category: Prediction
    subcategory: Prediction
    colors: list[Prediction] = Field(default_factory=list, max_length=8)
    attributes: dict[str, Prediction] = Field(default_factory=dict)
    style_features: list[Prediction] = Field(default_factory=list)
    visual_embedding: VisualEmbedding
    metadata: dict[str, str] = Field(default_factory=dict)
    verified_attributes: dict[str, str] = Field(default_factory=dict)
