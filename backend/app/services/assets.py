from collections.abc import Awaitable, Callable
from uuid import UUID

from app.models.assets import StoredAsset
from app.storage.assets import AssetStorage


class AssetService:
    def __init__(self, storage: AssetStorage) -> None:
        self._storage = storage

    async def ingest(
        self,
        user_id: UUID,
        filename: str,
        content_type: str,
        read: Callable[[int], Awaitable[bytes]],
    ) -> StoredAsset:
        return await self._storage.save(user_id, filename, content_type, read)

    async def delete(self, user_id: UUID, asset_id: UUID) -> None:
        await self._storage.delete(user_id, asset_id)
