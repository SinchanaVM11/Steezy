from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.assets import get_asset_service
from app.core.errors import ApiError
from app.main import app
from app.services.assets import AssetService
from app.storage.assets import (
    ALLOWED_IMAGE_TYPES,
    InMemoryAssetStorage,
    LocalFileAssetStorage,
    MAX_IMAGE_BYTES,
)


def test_upload_endpoint_returns_user_scoped_asset_reference(tmp_path: Path) -> None:
    app.dependency_overrides[get_asset_service] = lambda: AssetService(
        LocalFileAssetStorage(str(tmp_path))
    )
    try:
        user_id = uuid4()
        response = TestClient(app).post(
            "/assets/images",
            headers={"X-User-ID": str(user_id)},
            files={"file": ("shirt.png", b"pixels", "image/png")},
        )
    finally:
        app.dependency_overrides.pop(get_asset_service, None)

    assert response.status_code == 201
    body = response.json()
    assert body["user_id"] == str(user_id)
    assert body["storage_key"].startswith(f"{user_id}/")
    assert (tmp_path / body["storage_key"]).read_bytes() == b"pixels"


def test_upload_endpoint_returns_structured_type_error() -> None:
    response = TestClient(app).post(
        "/assets/images",
        headers={"X-User-ID": str(uuid4())},
        files={"file": ("notes.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_media_type"


async def reader(content: bytes, limit: int) -> bytes:
    return content[:limit]


@pytest.mark.anyio
async def test_local_storage_persists_and_isolates_assets(tmp_path: Path) -> None:
    storage = LocalFileAssetStorage(str(tmp_path))
    user_id = uuid4()
    asset = await storage.save(
        user_id, "shirt.png", "image/png", lambda limit: reader(b"pixels", limit)
    )

    assert (tmp_path / asset.storage_key).read_bytes() == b"pixels"
    assert asset.user_id == user_id
    await storage.delete(user_id, asset.asset_id)
    assert not (tmp_path / asset.storage_key).exists()


@pytest.mark.anyio
async def test_in_memory_storage_supports_isolated_test_cleanup() -> None:
    storage = InMemoryAssetStorage()
    user_id = uuid4()
    asset = await storage.save(
        user_id, "shirt.webp", "image/webp", lambda limit: reader(b"pixels", limit)
    )
    assert (user_id, asset.asset_id) in storage.assets
    await storage.delete(uuid4(), asset.asset_id)
    assert (user_id, asset.asset_id) in storage.assets


@pytest.mark.anyio
@pytest.mark.parametrize("content_type", ["text/plain", "image/gif", ""])
async def test_storage_rejects_unsupported_types(content_type: str) -> None:
    with pytest.raises(ApiError, match="Only JPEG"):
        await InMemoryAssetStorage().save(
            uuid4(), "file.bin", content_type, lambda limit: reader(b"x", limit)
        )


@pytest.mark.anyio
async def test_storage_rejects_traversal_and_oversized_content() -> None:
    storage = InMemoryAssetStorage()
    with pytest.raises(ApiError, match="path segments"):
        await storage.save(uuid4(), "../secret.png", "image/png", lambda limit: reader(b"x", limit))
    with pytest.raises(ApiError, match="5 MiB"):
        await storage.save(
            uuid4(), "large.png", "image/png",
            lambda limit: reader(b"x" * (MAX_IMAGE_BYTES + 1), limit),
        )
