from uuid import UUID

from fastapi import APIRouter, Depends, Header, status

from app.core.config import get_settings
from app.core.errors import ApiError
from app.schemas.analysis import AnalysisJobCreate, AnalysisJobResponse
from app.schemas.wardrobe import WardrobeItemResponse
from app.services.analysis import (
    AnalysisService,
    AssetNotFoundError,
    AssetNotOwnedError,
)
from app.api.assets import storage
from app.repositories.wardrobe import SQLiteWardrobeRepository
from app.services.materialization import MaterializationService
from app.repositories.vectors import SQLiteVectorRepository
from app.services.retrieval import RetrievalService

router = APIRouter(prefix="/analysis", tags=["analysis"])
wardrobe_repository = SQLiteWardrobeRepository(get_settings().database_path)
vector_repository = SQLiteVectorRepository(get_settings().database_path)
analysis_service = AnalysisService(storage)


def get_analysis_service() -> AnalysisService:
    return analysis_service


def get_materialization_service() -> MaterializationService:
    return MaterializationService(
        wardrobe_repository,
        storage,
        RetrievalService(vector_repository, wardrobe_repository),
    )


@router.post(
    "/garments",
    response_model=AnalysisJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Run the in-process garment metadata baseline",
    responses={
        404: {"description": "Asset missing or not owned"},
        422: {"description": "Invalid analysis request"},
        503: {"description": "Asset or analysis failure"},
    },
)
async def analyze_garment(
    request: AnalysisJobCreate,
    user_id: UUID = Header(..., alias="X-User-ID"),
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisJobResponse:
    try:
        return await service.analyze(request.asset_id, user_id)
    except AssetNotFoundError as error:
        raise ApiError("asset_not_found", str(error), 404) from error
    except AssetNotOwnedError as error:
        raise ApiError("asset_not_owned", str(error), 404) from error


@router.post(
    "/garments/{job_id}/wardrobe-item",
    response_model=WardrobeItemResponse,
    summary="Materialize a completed analysis into the wardrobe",
    responses={
        404: {"description": "Analysis missing or not owned"},
        409: {"description": "Analysis is not completed"},
        503: {"description": "Persistence failure"},
    },
)
async def materialize_garment(
    job_id: UUID,
    user_id: UUID = Header(..., alias="X-User-ID"),
    analysis: AnalysisService = Depends(get_analysis_service),
    materialization: MaterializationService = Depends(get_materialization_service),
) -> WardrobeItemResponse:
    job = analysis.get_job(job_id)
    if job is None:
        raise ApiError("analysis_not_found", "Analysis job was not found.", 404)
    return WardrobeItemResponse.model_validate(
        await materialization.materialize(job, user_id)
    )
