from uuid import UUID

from app.core.errors import ApiError
from app.models.vector import StoredEmbedding
from app.repositories.vectors import VectorRepository
from app.schemas.retrieval import (
    RetrievalMetadata,
    SimilaritySearchResponse,
    SimilaritySearchResult,
)
from app.schemas.representation import VisualEmbedding
from app.schemas.wardrobe import WardrobeItemResponse
from app.repositories.wardrobe import WardrobeRepository


class RetrievalService:
    def __init__(self, vectors: VectorRepository, wardrobe: WardrobeRepository) -> None:
        self._vectors = vectors
        self._wardrobe = wardrobe

    def index_item(self, item_id: UUID, user_id: UUID, representation: dict | None) -> None:
        if not representation or not representation.get("visual_embedding"):
            return
        embedding = representation["visual_embedding"]
        metadata = embedding["metadata"]
        values = tuple(float(value) for value in embedding["values"])
        dimension = int(metadata["dimension"])
        if dimension != len(values):
            raise ApiError("embedding_dimension_mismatch", "Embedding dimension does not match its values.", 422)
        item = self._wardrobe.get_for_user(item_id, user_id)
        if item is None:
            raise ApiError("item_not_found", "Wardrobe item was not found.", 404)
        self._vectors.upsert(
            StoredEmbedding(
                wardrobe_item_id=item_id,
                user_id=user_id,
                values=values,
                model_name=str(metadata["model_name"]),
                model_version=str(metadata["model_version"]),
                dimension=dimension,
                source=str(metadata["source"]),
                created_at=item.created_at,
            )
        )

    def search(
        self, user_id: UUID, embedding: list[float], top_k: int, threshold: float
    ) -> SimilaritySearchResponse:
        if not embedding:
            raise ApiError("invalid_embedding", "Embedding must not be empty.", 422)
        results = self._vectors.search(user_id, tuple(embedding), top_k, threshold)
        return self._response(embedding, results, user_id)

    def search_embedding(
        self,
        user_id: UUID,
        embedding: VisualEmbedding,
        top_k: int,
        threshold: float,
    ) -> SimilaritySearchResponse:
        metadata = embedding.metadata
        known = self._vectors.metadata_for_user(user_id)
        if known and not any(
            model == metadata.model_name
            and version == metadata.model_version
            and dimension == metadata.dimension
            and source == metadata.source
            for model, version, dimension, source in known
        ):
            raise ApiError(
                "embedding_model_incompatible",
                "Inspiration embedding is incompatible with the user's wardrobe embeddings.",
                422,
            )
        results = self._vectors.search(
            user_id,
            tuple(embedding.values),
            top_k,
            threshold,
            metadata.model_name,
            metadata.model_version,
        )
        return self._response(embedding.values, results, user_id)

    def _response(self, embedding, results, user_id):
        response = []
        for rank, (stored, score) in enumerate(results, start=1):
            item = self._wardrobe.get_for_user(stored.wardrobe_item_id, user_id)
            if item is None:
                continue
            response.append(
                SimilaritySearchResult(
                    item=WardrobeItemResponse.model_validate(item),
                    retrieval=RetrievalMetadata(
                        score=score,
                        model_name=stored.model_name,
                        model_version=stored.model_version,
                        dimension=stored.dimension,
                        source=stored.source,
                        created_at=stored.created_at,
                    ),
                    rank=rank,
                )
            )
        return SimilaritySearchResponse(query_dimension=len(embedding), results=response)
