from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.models.wardrobe import WardrobeItem
from app.repositories.wardrobe import WardrobeRepository
from app.schemas.wardrobe import WardrobeItemCreate


class WardrobeService:
    def __init__(self, repository: WardrobeRepository) -> None:
        self._repository = repository

    def create_item(self, data: WardrobeItemCreate) -> WardrobeItem:
        now = datetime.now(timezone.utc)
        item = WardrobeItem(
            id=uuid4(),
            user_id=data.user_id,
            category=data.category,
            subcategory=data.subcategory,
            colors=tuple(data.colors),
            source=data.source,
            verification_status="unverified",
            created_at=now,
            updated_at=now,
        )
        return self._repository.add(item)

    def list_items(self, user_id: UUID) -> list[WardrobeItem]:
        return list(self._repository.list_for_user(user_id))
