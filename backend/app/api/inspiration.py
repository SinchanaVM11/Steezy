from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, Query, UploadFile

from app.ai.embedding import VisualFeatureEmbedding
from app.api.analysis import vector_repository, wardrobe_repository
from app.api.assets import storage
from app.schemas.errors import ErrorResponse
from app.schemas.retrieval import SimilaritySearchResponse
from app.services.inspiration import InspirationRetrievalService
from app.services.retrieval import RetrievalService

router = APIRouter(prefix="/inspiration", tags=["inspiration"])


def get_inspiration_service() -> InspirationRetrievalService:
    return InspirationRetrievalService(
        storage,
        VisualFeatureEmbedding(),
        RetrievalService(vector_repository, wardrobe_repository),
        vector_repository,
    )


@router.post(
    "/search",
    response_model=SimilaritySearchResponse,
    summary="Retrieve a user's wardrobe from an inspiration image",
    responses={
        422: {"model": ErrorResponse, "description": "Invalid image, provider, or search parameters"},
        503: {"model": ErrorResponse, "description": "Vector persistence failure"},
    },
)
async def search_from_inspiration(
    user_id: UUID = Header(..., alias="X-User-ID"),
    file: UploadFile = File(...),
    top_k: int = Query(default=10, ge=1, le=100),
    similarity_threshold: float = Query(default=0.0, ge=-1, le=1),
    service: InspirationRetrievalService = Depends(get_inspiration_service),
) -> SimilaritySearchResponse:
    return await service.search(
        await file.read(),
        user_id,
        top_k,
        similarity_threshold,
        file.filename or "inspiration",
        file.content_type or "",
    )
