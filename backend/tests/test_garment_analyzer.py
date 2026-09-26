import pytest

from app.ai.garment_analyzer import (
    DeterministicMetadataAnalyzer,
    GarmentAnalysisInput,
)


def test_metadata_analyzer_normalizes_known_aliases_deterministically() -> None:
    result = DeterministicMetadataAnalyzer().analyze(
        GarmentAnalysisInput(category="  TShirt ", colors=[" Navy Blue ", "grey"])
    )

    assert result.category == "t-shirt"
    assert result.colors == ["navy", "gray"]
    assert result.unknown_attributes == []
    assert result.provider == "deterministic-metadata-baseline"


def test_metadata_analyzer_marks_unknown_category_without_fabricating_it() -> None:
    result = DeterministicMetadataAnalyzer().analyze(
        GarmentAnalysisInput(category="festival garment")
    )

    assert result.category == "festival garment"
    assert result.unknown_attributes == ["category"]


def test_metadata_analyzer_rejects_blank_category() -> None:
    with pytest.raises(ValueError):
        GarmentAnalysisInput(category=" ")
