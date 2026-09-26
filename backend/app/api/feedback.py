from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.config import get_settings
from app.repositories.feedback import SQLiteFeedbackRepository
from app.repositories.wardrobe import SQLiteWardrobeRepository
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.schemas.errors import ErrorResponse
from app.core.errors import ApiError
from app.services.feedback import (
    FeedbackService,
    WardrobeItemNotFoundError,
    WardrobeItemNotOwnedError,
)

router = APIRouter(prefix="/feedback", tags=["feedback"])
database_path = get_settings().database_path
feedback_repository = SQLiteFeedbackRepository(database_path)
wardrobe_repository = SQLiteWardrobeRepository(database_path)


def get_feedback_service() -> FeedbackService:
    return FeedbackService(feedback_repository, wardrobe_repository)


@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record an append-only feedback event",
    responses={
        404: {"model": ErrorResponse, "description": "Item missing or not owned"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        503: {"model": ErrorResponse, "description": "Persistence error"},
    },
)
def create_feedback(
    data: FeedbackCreate,
    service: FeedbackService = Depends(get_feedback_service),
) -> FeedbackResponse:
    try:
        return FeedbackResponse.model_validate(service.record(data))
    except WardrobeItemNotFoundError as error:
        raise ApiError("item_not_found", str(error), 404) from error
    except WardrobeItemNotOwnedError as error:
        raise ApiError("item_not_owned", str(error), 404) from error


@router.get(
    "",
    response_model=list[FeedbackResponse],
    summary="List a user's feedback events",
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        503: {"model": ErrorResponse, "description": "Persistence error"},
    },
)
def list_feedback(
    user_id: UUID = Query(...),
    service: FeedbackService = Depends(get_feedback_service),
) -> list[FeedbackResponse]:
    return [FeedbackResponse.model_validate(item) for item in service.list_for_user(user_id)]
