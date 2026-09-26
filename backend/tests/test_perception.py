from io import BytesIO

from PIL import Image

from app.ai.embedding import DeterministicByteEmbedding
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
    assert representation.visual_embedding.metadata.dimension == 8


def test_embedding_is_deterministic_and_normalized() -> None:
    embedding = DeterministicByteEmbedding()
    first = embedding.generate(b"same-image")
    second = embedding.generate(b"same-image")

    assert first == second
    assert first.metadata.model_name == "deterministic-byte-baseline"
    assert len(first.values) == first.metadata.dimension
    assert round(sum(value * value for value in first.values), 5) == 1
