from io import BytesIO

from PIL import Image

from app.ai.embedding import DeterministicByteEmbedding, VisualFeatureEmbedding
from app.ai.perception import DeterministicFashionPerception


def image_bytes(color: tuple[int, int, int]) -> bytes:
    output = BytesIO()
    Image.new("RGB", (4, 4), color).save(output, format="PNG")
    return output.getvalue()


def test_perception_extracts_color_and_preserves_unknowns() -> None:
    representation = DeterministicFashionPerception().analyze(
        image_bytes((20, 40, 180)), "shirt.png"
    )

    assert representation.category.value == "shirt"
    assert representation.category.confidence is None
    assert representation.colors[0].value == "blue"
    assert representation.attributes["material"].value == "unknown"
    assert representation.visual_embedding.metadata.dimension == 36


def test_embedding_is_deterministic_and_normalized() -> None:
    embedding = DeterministicByteEmbedding()
    first = embedding.generate(b"same-image")
    second = embedding.generate(b"same-image")

    assert first == second
    assert first.metadata.model_name == "deterministic-byte-baseline"
    assert len(first.values) == first.metadata.dimension
    assert round(sum(value * value for value in first.values), 5) == 1


def test_visual_embedding_is_image_sensitive_and_evaluated() -> None:
    embedding = VisualFeatureEmbedding()
    blue = embedding.generate(image_bytes((20, 40, 180)))
    red = embedding.generate(image_bytes((180, 40, 40)))
    repeat = embedding.generate(image_bytes((20, 40, 180)))

    assert blue == repeat
    assert blue.metadata.model_name == "visual-rgb-feature-baseline"
    assert blue.metadata.dimension == 36
    assert len(blue.values) == 36
    assert sum((left - right) ** 2 for left, right in zip(blue.values, red.values)) > 0.1
    assert round(sum(value * value for value in blue.values), 5) == 1
