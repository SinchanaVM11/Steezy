from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.config import get_settings
from app.repositories.wardrobe import SQLiteWardrobeRepository
from app.schemas.wardrobe import WardrobeItemCreate, WardrobeItemResponse
from app.services.wardrobe import WardrobeService

router = APIRouter(prefix="/wardrobe/items", tags=["wardrobe"])
repository = SQLiteWardrobeRepository(get_settings().database_path)


def get_wardrobe_service() -> WardrobeService:
    return WardrobeService(repository)


@router.post("", response_model=WardrobeItemResponse, status_code=status.HTTP_201_CREATED)
def create_wardrobe_item(
    data: WardrobeItemCreate,
    service: WardrobeService = Depends(get_wardrobe_service),
) -> WardrobeItemResponse:
    return WardrobeItemResponse.model_validate(service.create_item(data))


@router.get("", response_model=list[WardrobeItemResponse])
def list_wardrobe_items(
    user_id: UUID = Query(...),
    service: WardrobeService = Depends(get_wardrobe_service),
) -> list[WardrobeItemResponse]:
    return [
        WardrobeItemResponse.model_validate(item)
        for item in service.list_items(user_id)
    ]
