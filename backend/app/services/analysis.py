from uuid import UUID, uuid4

from app.ai.garment_analyzer import (
    GarmentAnalyzer,
    GarmentAnalysisInput,
    GarmentAnalysisResult,
)
from app.ai.perception import DeterministicFashionPerception, PerceptionService
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
        perception: PerceptionService | None = None,
    ) -> None:
        self._storage = storage
        self._analyzer = analyzer
        self._perception = perception or DeterministicFashionPerception()
        self._jobs: dict[UUID, AnalysisJobResponse] = {}

    async def analyze(self, asset_id: UUID, user_id: UUID) -> AnalysisJobResponse:
        asset = await self._storage.get(asset_id)
        if asset is None:
            raise AssetNotFoundError("asset was not found")
        if asset.user_id != user_id:
            raise AssetNotOwnedError("asset is not owned by user")
        try:
            image_bytes = await self._storage.read(asset)
            if self._analyzer is not None:
                category = asset.original_filename.rsplit(".", 1)[0].replace("_", " ")
                legacy = self._analyzer.analyze(
                    GarmentAnalysisInput(category=category or "unknown")
                )
                result = legacy
            else:
                representation = self._perception.analyze(
                    image_bytes, asset.original_filename
                )
                result = GarmentAnalysisResult(
                    category=representation.category.value,
                    colors=[color.value for color in representation.colors],
                    unknown_attributes=[
                        name
                        for name, prediction in representation.attributes.items()
                        if prediction.value == "unknown"
                    ],
                    provider=representation.category.source,
                    representation=representation,
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
