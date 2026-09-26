from uuid import UUID

from fastapi import APIRouter, Depends, Header

from app.api.analysis import vector_repository, wardrobe_repository
from app.schemas.errors import ErrorResponse
from app.schemas.retrieval import SimilaritySearchRequest, SimilaritySearchResponse
from app.services.retrieval import RetrievalService

router = APIRouter(prefix="/wardrobe", tags=["retrieval"])


def get_retrieval_service() -> RetrievalService:
    return RetrievalService(vector_repository, wardrobe_repository)


@router.post(
    "/search",
    response_model=SimilaritySearchResponse,
    summary="Retrieve visually similar wardrobe items",
    responses={
        422: {"model": ErrorResponse, "description": "Invalid embedding or search parameters"},
        503: {"model": ErrorResponse, "description": "Vector persistence failure"},
    },
)
def search_wardrobe(
    request: SimilaritySearchRequest,
    user_id: UUID = Header(..., alias="X-User-ID"),
    service: RetrievalService = Depends(get_retrieval_service),
) -> SimilaritySearchResponse:
    return service.search(
        user_id, request.embedding, request.top_k, request.similarity_threshold
    )
