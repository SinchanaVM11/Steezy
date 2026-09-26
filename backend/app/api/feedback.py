from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.config import get_settings
from app.repositories.feedback import SQLiteFeedbackRepository
from app.repositories.wardrobe import SQLiteWardrobeRepository
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.feedback import FeedbackService, WardrobeItemNotOwnedError

router = APIRouter(prefix="/feedback", tags=["feedback"])
database_path = get_settings().database_path
feedback_repository = SQLiteFeedbackRepository(database_path)
wardrobe_repository = SQLiteWardrobeRepository(database_path)


def get_feedback_service() -> FeedbackService:
    return FeedbackService(feedback_repository, wardrobe_repository)


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(
    data: FeedbackCreate,
    service: FeedbackService = Depends(get_feedback_service),
) -> FeedbackResponse:
    try:
        return FeedbackResponse.model_validate(service.record(data))
    except WardrobeItemNotOwnedError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("", response_model=list[FeedbackResponse])
def list_feedback(
    user_id: UUID = Query(...),
    service: FeedbackService = Depends(get_feedback_service),
) -> list[FeedbackResponse]:
    return [FeedbackResponse.model_validate(item) for item in service.list_for_user(user_id)]
