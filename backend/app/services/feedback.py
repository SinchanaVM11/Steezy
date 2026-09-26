from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.models.feedback import Feedback
from app.repositories.feedback import FeedbackRepository
from app.repositories.wardrobe import WardrobeRepository
from app.schemas.feedback import FeedbackCreate


class WardrobeItemNotOwnedError(ValueError):
    """Raised when feedback references another user's or missing item."""


class FeedbackService:
    def __init__(
        self,
        feedback_repository: FeedbackRepository,
        wardrobe_repository: WardrobeRepository,
    ) -> None:
        self._feedback_repository = feedback_repository
        self._wardrobe_repository = wardrobe_repository

    def record(self, data: FeedbackCreate) -> Feedback:
        if self._wardrobe_repository.get_for_user(
            data.wardrobe_item_id, data.user_id
        ) is None:
            raise WardrobeItemNotOwnedError("wardrobe item is not owned by user")
        feedback = Feedback(
            id=uuid4(),
            user_id=data.user_id,
            wardrobe_item_id=data.wardrobe_item_id,
            action=data.action.value,
            context=data.context,
            created_at=datetime.now(timezone.utc),
        )
        return self._feedback_repository.add(feedback)

    def list_for_user(self, user_id: UUID) -> list[Feedback]:
        return list(self._feedback_repository.list_for_user(user_id))
