from collections.abc import Awaitable, Callable
from pathlib import Path, PurePath
from typing import Protocol
from uuid import UUID, uuid4

from app.core.errors import ApiError
from app.models.assets import StoredAsset

MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})


class AssetStorage(Protocol):
    async def save(
        self,
        user_id: UUID,
        filename: str,
        content_type: str,
        read: Callable[[int], Awaitable[bytes]],
    ) -> StoredAsset: ...

    async def delete(self, user_id: UUID, asset_id: UUID) -> None: ...

    async def get(self, asset_id: UUID) -> StoredAsset | None: ...

    async def read(self, asset: StoredAsset) -> bytes: ...


def validate_filename(filename: str) -> str:
    name = Path(filename).name
    if not filename or name != filename or name in {".", ".."}:
        raise ApiError("unsafe_filename", "Filename must not contain path segments.", 422)
    if not name.strip():
        raise ApiError("unsafe_filename", "Filename must not be blank.", 422)
    return name


def validate_content_type(content_type: str) -> None:
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ApiError("unsupported_media_type", "Only JPEG, PNG, and WebP images are allowed.", 415)


class InMemoryAssetStorage:
    def __init__(self) -> None:
        self.assets: dict[tuple[UUID, UUID], tuple[StoredAsset, bytes]] = {}

    async def save(self, user_id, filename, content_type, read):
        filename = validate_filename(filename)
        validate_content_type(content_type)
        content = await read(MAX_IMAGE_BYTES + 1)
        if len(content) > MAX_IMAGE_BYTES:
            raise ApiError("file_too_large", "Image exceeds the 5 MiB limit.", 413)
        asset_id = uuid4()
        asset = StoredAsset(
            asset_id=asset_id,
            user_id=user_id,
            content_type=content_type,
            size_bytes=len(content),
            original_filename=filename,
            storage_key=f"memory/{user_id}/{asset_id}",
        )
        self.assets[(user_id, asset_id)] = (asset, content)
        return asset

    async def delete(self, user_id, asset_id):
        self.assets.pop((user_id, asset_id), None)

    async def get(self, asset_id):
        return next((asset for asset, _ in self.assets.values() if asset.asset_id == asset_id), None)

    async def read(self, asset):
        stored = self.assets.get((asset.user_id, asset.asset_id))
        if stored is None:
            raise ApiError("asset_not_found", "Asset bytes were not found.", 404)
        return stored[1]


class LocalFileAssetStorage:
    def __init__(self, root: str) -> None:
        self._root = Path(root).resolve()
        self._assets: dict[UUID, StoredAsset] = {}

    async def save(self, user_id, filename, content_type, read):
        filename = validate_filename(filename)
        validate_content_type(content_type)
        content = await read(MAX_IMAGE_BYTES + 1)
        if len(content) > MAX_IMAGE_BYTES:
            raise ApiError("file_too_large", "Image exceeds the 5 MiB limit.", 413)
        asset_id = uuid4()
        user_dir = self._root / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        storage_key = PurePath(str(user_id), f"{asset_id}.bin").as_posix()
        destination = (self._root / storage_key).resolve()
        if self._root not in destination.parents:
            raise ApiError("storage_error", "Generated storage path escaped the asset root.", 503)
        try:
            destination.write_bytes(content)
        except OSError as error:
            raise ApiError("storage_error", "Asset storage failed.", 503) from error
        asset = StoredAsset(asset_id, user_id, content_type, len(content), filename, storage_key)
        self._assets[asset_id] = asset
        return asset

    async def delete(self, user_id, asset_id):
        destination = (self._root / str(user_id) / f"{asset_id}.bin").resolve()
        if self._root not in destination.parents:
            raise ApiError("storage_error", "Invalid asset reference.", 503)
        try:
            destination.unlink(missing_ok=True)
        except OSError as error:
            raise ApiError("storage_error", "Asset cleanup failed.", 503) from error

    async def get(self, asset_id):
        return self._assets.get(asset_id)

    async def read(self, asset):
        destination = (self._root / asset.storage_key).resolve()
        if self._root not in destination.parents or not destination.is_file():
            raise ApiError("asset_not_found", "Asset bytes were not found.", 404)
        try:
            return destination.read_bytes()
        except OSError as error:
            raise ApiError("storage_error", "Asset read failed.", 503) from error
