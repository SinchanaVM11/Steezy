from uuid import UUID

from app.ai.embedding import EmbeddingService
from app.core.errors import ApiError
from app.repositories.vectors import VectorRepository
from app.services.retrieval import RetrievalService
from app.storage.assets import AssetStorage
from app.storage.assets import MAX_IMAGE_BYTES, validate_content_type, validate_filename


class InspirationRetrievalService:
    """Image query orchestration; ranking remains cosine retrieval only."""

    def __init__(
        self,
        storage: AssetStorage,
        embedding: EmbeddingService,
        retrieval: RetrievalService,
        vectors: VectorRepository,
    ) -> None:
        self._storage = storage
        self._embedding = embedding
        self._retrieval = retrieval
        self._vectors = vectors

    async def search(
        self,
        image_bytes: bytes,
        user_id: UUID,
        top_k: int,
        threshold: float,
        filename: str = "inspiration",
        content_type: str = "image/jpeg",
    ):
        if not image_bytes:
            raise ApiError("invalid_image", "Inspiration image is empty.", 422)
        validate_filename(filename)
        validate_content_type(content_type)
        if len(image_bytes) > MAX_IMAGE_BYTES:
            raise ApiError("file_too_large", "Inspiration image exceeds the 5 MiB limit.", 413)
        try:
            query = self._embedding.generate(image_bytes)
        except (ValueError, OSError) as error:
            raise ApiError("invalid_image", "Inspiration image could not be processed.", 422) from error
        return self._retrieval.search_embedding(user_id, query, top_k, threshold)
