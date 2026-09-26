from io import BytesIO
from pathlib import Path
from typing import Protocol

from PIL import Image, UnidentifiedImageError

from app.ai.embedding import EmbeddingService, VisualFeatureEmbedding
from app.schemas.representation import FashionItemRepresentation, Prediction


class PerceptionService(Protocol):
    def analyze(self, image_bytes: bytes, filename: str) -> FashionItemRepresentation: ...


class DeterministicFashionPerception:
    """Image-aware baseline; it is not CLIP or production garment detection."""

    source = "deterministic-fashion-perception-baseline"
    model_version = "1"
    _known_categories = {"shirt", "t-shirt", "trousers", "shoes", "dress", "jacket"}
    _color_names = (
        ((40, 40, 40), "black"),
        ((220, 220, 220), "white"),
        ((150, 150, 150), "gray"),
        ((180, 40, 40), "red"),
        ((40, 90, 180), "blue"),
        ((40, 140, 70), "green"),
        ((210, 170, 40), "yellow"),
        ((150, 80, 35), "brown"),
    )

    def __init__(self, embedding: EmbeddingService | None = None) -> None:
        self._embedding = embedding or VisualFeatureEmbedding()

    def analyze(self, image_bytes: bytes, filename: str) -> FashionItemRepresentation:
        try:
            with Image.open(BytesIO(image_bytes)) as image:
                image = image.convert("RGB")
                image.thumbnail((128, 128))
                pixels = list(
                    image.get_flattened_data()
                    if hasattr(image, "get_flattened_data")
                    else image.getdata()
                )
        except (UnidentifiedImageError, OSError) as error:
            raise ValueError("image preprocessing failed") from error
        if not pixels:
            raise ValueError("image contains no pixels")

        stem = Path(filename).stem.replace("_", " ").strip().lower() or "unknown"
        category = stem if stem in self._known_categories else "unknown"
        category_confidence = None
        colors = [
            Prediction(
                value=self._nearest_color(pixels),
                confidence=None,
                source=self.source,
                model_name="rgb-quantization-baseline",
                model_version=self.model_version,
            )
        ]
        return FashionItemRepresentation(
            category=Prediction(
                value=category,
                confidence=category_confidence,
                source=self.source,
                model_name="filename-category-baseline",
                model_version=self.model_version,
            ),
            subcategory=Prediction(
                value="unknown", confidence=None, source=self.source, model_version=self.model_version
            ),
            colors=colors,
            attributes={
                "pattern": Prediction(
                    value="unknown", confidence=None, source=self.source, model_version=self.model_version
                ),
                "material": Prediction(
                    value="unknown", confidence=None, source=self.source, model_version=self.model_version
                ),
            },
            style_features=[],
            visual_embedding=self._embedding.generate(image_bytes),
            metadata={
                "preprocessing": "RGB conversion and 128px thumbnail",
                "input_filename": filename,
            },
        )

    def _nearest_color(self, pixels: list[tuple[int, int, int]]) -> str:
        average = tuple(sum(pixel[index] for pixel in pixels) // len(pixels) for index in range(3))
        return min(
            self._color_names,
            key=lambda candidate: sum((average[index] - candidate[0][index]) ** 2 for index in range(3)),
        )[1]
