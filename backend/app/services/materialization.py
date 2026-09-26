from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.core.errors import ApiError
from app.models.wardrobe import WardrobeItem
from app.repositories.wardrobe import WardrobeRepository
from app.schemas.analysis import AnalysisJobResponse, AnalysisStatus
from app.storage.assets import AssetStorage
from app.services.retrieval import RetrievalService


class MaterializationService:
    def __init__(
        self,
        wardrobe_repository: WardrobeRepository,
        storage: AssetStorage,
        retrieval: RetrievalService | None = None,
    ) -> None:
        self._wardrobe_repository = wardrobe_repository
        self._storage = storage
        self._retrieval = retrieval

    async def materialize(
        self,
        job: AnalysisJobResponse,
        user_id: UUID,
    ) -> WardrobeItem:
        if job.user_id != user_id:
            raise ApiError("analysis_not_owned", "Analysis job is not owned by user.", 404)
        if job.status != AnalysisStatus.COMPLETED or job.result is None:
            raise ApiError("analysis_not_completed", "Analysis job is not completed.", 409)
        asset = await self._storage.get(job.asset_id)
        if asset is None or asset.user_id != user_id:
            raise ApiError("asset_not_found", "Analysis asset was not found.", 404)
        existing = self._wardrobe_repository.get_by_analysis_job_for_user(
            job.job_id, user_id
        )
        if existing is not None:
            return existing
        now = datetime.now(timezone.utc)
        item = WardrobeItem(
            id=uuid4(),
            user_id=user_id,
            category=job.result.category,
            subcategory=None,
            colors=tuple(job.result.colors),
            source="imported",
            verification_status="unverified",
            asset_id=job.asset_id,
            analysis_job_id=job.job_id,
            analysis_provider=job.result.provider,
            analysis_unknown_attributes=tuple(job.result.unknown_attributes),
            created_at=now,
            updated_at=now,
            representation=job.result.representation.model_dump()
            if job.result.representation is not None
            else None,
            verified_attributes={},
        )
        try:
            created = self._wardrobe_repository.add(item)
            if self._retrieval is not None:
                self._retrieval.index_item(
                    created.id, created.user_id, created.representation
                )
            return created
        except ApiError:
            raise
        except Exception as error:
            raise ApiError("persistence_error", "Wardrobe persistence failed.", 503) from error
