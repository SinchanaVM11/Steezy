import hashlib
import math
from typing import Protocol

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
