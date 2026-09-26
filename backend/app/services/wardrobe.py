from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.ai.garment_analyzer import (
    DeterministicMetadataAnalyzer,
    GarmentAnalyzer,
    GarmentAnalysisInput,
)
from app.models.wardrobe import WardrobeItem
from app.repositories.wardrobe import WardrobeRepository
from app.schemas.wardrobe import WardrobeItemCreate


class WardrobeService:
    def __init__(
        self,
        repository: WardrobeRepository,
        analyzer: GarmentAnalyzer | None = None,
    ) -> None:
        self._repository = repository
        self._analyzer = analyzer or DeterministicMetadataAnalyzer()

    def create_item(self, data: WardrobeItemCreate) -> WardrobeItem:
        analysis = self._analyzer.analyze(
            GarmentAnalysisInput(category=data.category, colors=data.colors)
        )
        now = datetime.now(timezone.utc)
        item = WardrobeItem(
            id=uuid4(),
            user_id=data.user_id,
            category=analysis.category,
            subcategory=data.subcategory,
            colors=tuple(analysis.colors),
            source=data.source,
            verification_status="unverified",
            created_at=now,
            updated_at=now,
        )
        return self._repository.add(item)

    def list_items(self, user_id: UUID) -> list[WardrobeItem]:
        return list(self._repository.list_for_user(user_id))
