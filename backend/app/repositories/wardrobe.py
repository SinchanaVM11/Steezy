from collections.abc import Iterable
from typing import Protocol
from uuid import UUID

from app.models.wardrobe import WardrobeItem


class WardrobeRepository(Protocol):
    def add(self, item: WardrobeItem) -> WardrobeItem: ...

    def list_for_user(self, user_id: UUID) -> Iterable[WardrobeItem]: ...


class InMemoryWardrobeRepository:
    """Development adapter; data is lost when the API process stops."""

    def __init__(self) -> None:
        self._items: dict[UUID, WardrobeItem] = {}

    def add(self, item: WardrobeItem) -> WardrobeItem:
        self._items[item.id] = item
        return item

    def list_for_user(self, user_id: UUID) -> list[WardrobeItem]:
        return [item for item in self._items.values() if item.user_id == user_id]
