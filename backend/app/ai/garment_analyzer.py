from typing import Protocol

from pydantic import BaseModel, Field, field_validator


class GarmentAnalysisInput(BaseModel):
    category: str = Field(min_length=1, max_length=80)
    colors: list[str] = Field(default_factory=list, max_length=8)

    @field_validator("category")
    @classmethod
    def category_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("category must not be blank")
        return value


class GarmentAnalysisResult(BaseModel):
    category: str
    colors: list[str]
    unknown_attributes: list[str]
    provider: str


class GarmentAnalyzer(Protocol):
    def analyze(self, data: GarmentAnalysisInput) -> GarmentAnalysisResult: ...


class DeterministicMetadataAnalyzer:
    """Safe metadata baseline; this does not inspect images or claim confidence."""

    provider = "deterministic-metadata-baseline"
    _category_aliases = {
        "tee": "t-shirt",
        "tshirt": "t-shirt",
        "t shirt": "t-shirt",
        "pant": "trousers",
        "pants": "trousers",
    }
    _color_aliases = {
        "grey": "gray",
        "navy blue": "navy",
        "off-white": "white",
    }

    def analyze(self, data: GarmentAnalysisInput) -> GarmentAnalysisResult:
        category = self._normalize(data.category)
        colors = [self._normalize(color) for color in data.colors]
        unknown_attributes = []
        if category not in {"shirt", "t-shirt", "trousers", "shoes", "dress", "jacket"}:
            unknown_attributes.append("category")
        return GarmentAnalysisResult(
            category=category,
            colors=colors,
            unknown_attributes=unknown_attributes,
            provider=self.provider,
        )

    def _normalize(self, value: str) -> str:
        normalized = " ".join(value.strip().lower().split())
        return self._category_aliases.get(
            normalized,
            self._color_aliases.get(normalized, normalized),
        )
