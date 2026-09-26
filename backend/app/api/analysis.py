from uuid import UUID

from fastapi import APIRouter, Depends, Header, status

from app.core.config import get_settings
from app.core.errors import ApiError
from app.schemas.analysis import AnalysisJobCreate, AnalysisJobResponse
from app.services.analysis import (
    AnalysisService,
    AssetNotFoundError,
    AssetNotOwnedError,
)
from app.storage.assets import LocalFileAssetStorage

router = APIRouter(prefix="/analysis", tags=["analysis"])
storage = LocalFileAssetStorage(get_settings().asset_storage_path)


def get_analysis_service() -> AnalysisService:
    return AnalysisService(storage)


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
