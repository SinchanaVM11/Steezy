from uuid import uuid4

import pytest

from app.core.errors import ApiError
from app.api.assets import get_asset_service
from app.api.analysis import get_analysis_service, get_materialization_service
from app.main import app
from app.repositories.wardrobe import InMemoryWardrobeRepository, SQLiteWardrobeRepository
from app.services.assets import AssetService
from app.services.analysis import AnalysisService
from app.services.materialization import MaterializationService
from app.schemas.analysis import AnalysisJobResponse, AnalysisResult, AnalysisStatus


async def read_pixels(_: int) -> bytes:
    return b"pixels"


def completed_job(user_id, status=AnalysisStatus.COMPLETED):
    return AnalysisJobResponse(
        job_id=uuid4(),
        asset_id=uuid4(),
        user_id=user_id,
        status=status,
        result=(
            AnalysisResult(
                category="shirt",
                colors=["navy"],
                unknown_attributes=["material"],
                provider="deterministic-metadata-baseline",
            )
            if status == AnalysisStatus.COMPLETED
            else None
        ),
        error_code=None if status == AnalysisStatus.COMPLETED else "analysis_failed",
    )


@pytest.mark.anyio
async def test_materialization_preserves_asset_and_analysis_provenance() -> None:
    user_id = uuid4()
    job = completed_job(user_id)
    repository = InMemoryWardrobeRepository()
    from app.storage.assets import InMemoryAssetStorage
    storage = InMemoryAssetStorage()
    asset = await storage.save(user_id, "shirt.png", "image/png", read_pixels)
    job.asset_id = asset.asset_id
    item = await MaterializationService(repository, storage).materialize(job, user_id)

    assert item.asset_id == job.asset_id
    assert item.analysis_job_id == job.job_id
    assert item.analysis_provider == "deterministic-metadata-baseline"
    assert item.analysis_unknown_attributes == ("material",)
    assert item.source == "imported"


@pytest.mark.anyio
async def test_materialization_is_idempotent_and_user_scoped() -> None:
    user_id = uuid4()
    job = completed_job(user_id)
    repository = InMemoryWardrobeRepository()
    from app.storage.assets import InMemoryAssetStorage
    storage = InMemoryAssetStorage()
    asset = await storage.save(user_id, "shirt.png", "image/png", read_pixels)
    job.asset_id = asset.asset_id
    service = MaterializationService(repository, storage)

    first = await service.materialize(job, user_id)
    second = await service.materialize(job, user_id)

    assert first == second
    with pytest.raises(ApiError, match="not owned"):
        await service.materialize(job, uuid4())


@pytest.mark.anyio
async def test_materialization_rejects_incomplete_or_missing_result() -> None:
    user_id = uuid4()
    repository = InMemoryWardrobeRepository()
    from app.storage.assets import InMemoryAssetStorage
    service = MaterializationService(repository, InMemoryAssetStorage())

    with pytest.raises(ApiError, match="not completed"):
        await service.materialize(completed_job(user_id, AnalysisStatus.FAILED), user_id)


@pytest.mark.anyio
async def test_sqlite_materialization_persists_and_reloads(tmp_path) -> None:
    user_id = uuid4()
    job = completed_job(user_id)
    path = str(tmp_path / "wardrobe.sqlite3")
    from app.storage.assets import InMemoryAssetStorage
    storage = InMemoryAssetStorage()
    asset = await storage.save(user_id, "shirt.png", "image/png", read_pixels)
    job.asset_id = asset.asset_id
    await MaterializationService(SQLiteWardrobeRepository(path), storage).materialize(
        job, user_id
    )

    reloaded = SQLiteWardrobeRepository(path).get_by_analysis_job_for_user(
        job.job_id, user_id
    )

    assert reloaded is not None
    assert reloaded.asset_id == job.asset_id
    assert reloaded.analysis_unknown_attributes == ("material",)


def test_endpoint_pipeline_uploads_analyzes_and_materializes(tmp_path) -> None:
    from app.storage.assets import LocalFileAssetStorage

    storage = LocalFileAssetStorage(str(tmp_path / "assets"))
    wardrobe_path = str(tmp_path / "wardrobe.sqlite3")
    analysis_service = AnalysisService(storage)
    materialization = MaterializationService(
        SQLiteWardrobeRepository(wardrobe_path), storage
    )
    app.dependency_overrides[get_asset_service] = lambda: AssetService(storage)
    app.dependency_overrides[get_analysis_service] = lambda: analysis_service
    app.dependency_overrides[get_materialization_service] = lambda: materialization
    try:
        from fastapi.testclient import TestClient

        user_id = uuid4()
        client = TestClient(app)
        uploaded = client.post(
            "/assets/images",
            headers={"X-User-ID": str(user_id)},
            files={"file": ("shirt.png", b"pixels", "image/png")},
        )
        analyzed = client.post(
            "/analysis/garments",
            headers={"X-User-ID": str(user_id)},
            json={"asset_id": uploaded.json()["asset_id"]},
        )
        materialized = client.post(
            f"/analysis/garments/{analyzed.json()['job_id']}/wardrobe-item",
            headers={"X-User-ID": str(user_id)},
        )
    finally:
        app.dependency_overrides.clear()

    assert uploaded.status_code == 201
    assert analyzed.status_code == 200
    assert analyzed.json()["status"] == "completed"
    assert materialized.status_code == 200
    assert materialized.json()["asset_id"] == uploaded.json()["asset_id"]
