from pathlib import Path
from uuid import UUID, uuid4

from app.ai.garment_analyzer import (
    DeterministicMetadataAnalyzer,
    GarmentAnalysisInput,
    GarmentAnalyzer,
)
from app.core.errors import ApiError
from app.models.assets import StoredAsset
from app.schemas.analysis import AnalysisJobResponse, AnalysisStatus
from app.storage.assets import AssetStorage


class AssetNotFoundError(ValueError):
    pass


class AssetNotOwnedError(ValueError):
    pass


class AnalysisService:
    def __init__(
        self,
        storage: AssetStorage,
        analyzer: GarmentAnalyzer | None = None,
    ) -> None:
        self._storage = storage
        self._analyzer = analyzer or DeterministicMetadataAnalyzer()
        self._jobs: dict[UUID, AnalysisJobResponse] = {}

    async def analyze(self, asset_id: UUID, user_id: UUID) -> AnalysisJobResponse:
        asset = await self._storage.get(asset_id)
        if asset is None:
            raise AssetNotFoundError("asset was not found")
        if asset.user_id != user_id:
            raise AssetNotOwnedError("asset is not owned by user")
        try:
            await self._storage.read(asset)
            category = Path(asset.original_filename).stem.replace("_", " ")
            result = self._analyzer.analyze(
                GarmentAnalysisInput(category=category or "unknown")
            )
            job = AnalysisJobResponse(
                job_id=uuid4(),
                asset_id=asset.asset_id,
                user_id=user_id,
                status=AnalysisStatus.COMPLETED,
                result=result.model_dump(),
            )
            self._jobs[job.job_id] = job
            return job
        except ApiError:
            raise
        except Exception as error:
            job = AnalysisJobResponse(
                job_id=uuid4(),
                asset_id=asset.asset_id,
                user_id=user_id,
                status=AnalysisStatus.FAILED,
                result=None,
                error_code="analysis_failed",
            )
            self._jobs[job.job_id] = job
            return job

    def get_job(self, job_id: UUID) -> AnalysisJobResponse | None:
        return self._jobs.get(job_id)
