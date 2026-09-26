from uuid import uuid4

import pytest

from app.schemas.analysis import AnalysisStatus
from app.services.analysis import AnalysisService, AssetNotFoundError, AssetNotOwnedError
from app.storage.assets import InMemoryAssetStorage


async def reader(content: bytes, limit: int) -> bytes:
    return content[:limit]


@pytest.mark.anyio
async def test_analysis_is_deterministic_and_user_scoped() -> None:
    storage = InMemoryAssetStorage()
    user_id = uuid4()
    asset = await storage.save(
        user_id, "navy_shirt.png", "image/png", lambda limit: reader(b"pixels", limit)
    )
    service = AnalysisService(storage)

    first = await service.analyze(asset.asset_id, user_id)
    second = await service.analyze(asset.asset_id, user_id)

    assert first.status == AnalysisStatus.COMPLETED
    assert first.result == second.result
    assert first.result.category == "navy shirt"
    assert first.result.provider == "deterministic-metadata-baseline"
    with pytest.raises(AssetNotOwnedError):
        await service.analyze(asset.asset_id, uuid4())


@pytest.mark.anyio
async def test_analysis_rejects_missing_asset() -> None:
    with pytest.raises(AssetNotFoundError):
        await AnalysisService(InMemoryAssetStorage()).analyze(uuid4(), uuid4())


@pytest.mark.anyio
async def test_analysis_returns_failed_status_when_analyzer_fails() -> None:
    class BrokenAnalyzer:
        def analyze(self, data):
            raise RuntimeError("broken")

    storage = InMemoryAssetStorage()
    user_id = uuid4()
    asset = await storage.save(
        user_id, "shirt.png", "image/png", lambda limit: reader(b"pixels", limit)
    )

    result = await AnalysisService(storage, BrokenAnalyzer()).analyze(asset.asset_id, user_id)

    assert result.status == AnalysisStatus.FAILED
    assert result.result is None
    assert result.error_code == "analysis_failed"


@pytest.mark.anyio
async def test_analysis_surfaces_missing_bytes_without_partial_result() -> None:
    storage = InMemoryAssetStorage()
    user_id = uuid4()
    asset = await storage.save(
        user_id, "shirt.png", "image/png", lambda limit: reader(b"pixels", limit)
    )
    await storage.delete(user_id, asset.asset_id)

    with pytest.raises(AssetNotFoundError):
        await AnalysisService(storage).analyze(asset.asset_id, user_id)
