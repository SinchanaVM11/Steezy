import hashlib
import math
from io import BytesIO
from typing import Protocol

from PIL import Image, UnidentifiedImageError

from app.schemas.representation import EmbeddingMetadata, VisualEmbedding


class EmbeddingService(Protocol):
    def generate(self, image_bytes: bytes) -> VisualEmbedding: ...


class DeterministicByteEmbedding:
    """Reproducible placeholder, not a learned visual representation."""

    model_name = "deterministic-byte-baseline"
    model_version = "1"
    dimension = 8

    def generate(self, image_bytes: bytes) -> VisualEmbedding:
        digest = hashlib.sha256(image_bytes).digest()
        values = [
            round((int.from_bytes(digest[index : index + 2], "big") / 65535) * 2 - 1, 6)
            for index in range(0, self.dimension * 2, 2)
        ]
        norm = math.sqrt(sum(value * value for value in values)) or 1
        return VisualEmbedding(
            values=[round(value / norm, 6) for value in values],
            metadata=EmbeddingMetadata(
                model_name=self.model_name,
                model_version=self.model_version,
                dimension=self.dimension,
                source="deterministic-byte-baseline",
            ),
        )


class VisualFeatureEmbedding:
    """Offline image-derived baseline for low-level visual similarity."""

    model_name = "visual-rgb-feature-baseline"
    model_version = "1"
    dimension = 36

    def generate(self, image_bytes: bytes) -> VisualEmbedding:
        try:
            with Image.open(BytesIO(image_bytes)) as image:
                image = image.convert("RGB")
                image.thumbnail((128, 128))
                pixels = list(
                    image.get_flattened_data()
                    if hasattr(image, "get_flattened_data")
                    else image.getdata()
                )
                width, height = image.size
        except (UnidentifiedImageError, OSError) as error:
            raise ValueError("image preprocessing failed") from error
        if not pixels or not width or not height:
            raise ValueError("image contains no pixels")

        values: list[float] = []
        for channel in range(3):
            histogram = [0] * 8
            for pixel in pixels:
                histogram[min(pixel[channel] // 32, 7)] += 1
            values.extend(count / len(pixels) for count in histogram)

        for row in range(2):
            for column in range(2):
                crop = [
                    pixel
                    for index, pixel in enumerate(pixels)
                    if (index % width) * 2 // width == column
                    and (index // width) * 2 // height == row
                ]
                values.extend(
                    sum(pixel[channel] for pixel in crop) / (255 * len(crop))
                    for channel in range(3)
                )

        norm = math.sqrt(sum(value * value for value in values)) or 1
        return VisualEmbedding(
            values=[round(value / norm, 6) for value in values],
            metadata=EmbeddingMetadata(
                model_name=self.model_name,
                model_version=self.model_version,
                dimension=self.dimension,
                source="visual-feature-baseline",
            ),
        )
