from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, UploadFile, status

from app.core.config import get_settings
from app.schemas.assets import AssetResponse
from app.schemas.errors import ErrorResponse
from app.services.assets import AssetService
from app.storage.assets import LocalFileAssetStorage

router = APIRouter(prefix="/assets", tags=["assets"])
storage = LocalFileAssetStorage(get_settings().asset_storage_path)


def get_asset_service() -> AssetService:
    return AssetService(storage)


@router.post(
    "/images",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store a user-scoped garment image",
    responses={
        413: {"model": ErrorResponse, "description": "Image exceeds the size limit"},
        415: {"model": ErrorResponse, "description": "Unsupported image content type"},
        422: {"model": ErrorResponse, "description": "Invalid user or filename"},
        503: {"model": ErrorResponse, "description": "Asset storage failure"},
    },
)
async def upload_image(
    user_id: UUID = Header(..., alias="X-User-ID"),
    file: UploadFile = File(...),
    service: AssetService = Depends(get_asset_service),
) -> AssetResponse:
    asset = await service.ingest(
        user_id,
        file.filename or "",
        file.content_type or "",
        file.read,
    )
    return AssetResponse.model_validate(asset)
