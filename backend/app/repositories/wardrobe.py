import json
import sqlite3
from collections.abc import Iterable
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.models.wardrobe import WardrobeItem
from app.db.sqlite import initialize_database


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


class SQLiteWardrobeRepository:
    """Durable local adapter; PostgreSQL can replace it behind the same protocol."""

    def __init__(self, database_path: str) -> None:
        self._database_path = database_path
        initialize_database(database_path)

    def add(self, item: WardrobeItem) -> WardrobeItem:
        with sqlite3.connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO wardrobe_items
                (id, user_id, category, subcategory, colors, source,
                 verification_status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(item.id),
                    str(item.user_id),
                    item.category,
                    item.subcategory,
                    json.dumps(item.colors),
                    item.source,
                    item.verification_status,
                    item.created_at.isoformat(),
                    item.updated_at.isoformat(),
                ),
            )
        return item

    def list_for_user(self, user_id: UUID) -> list[WardrobeItem]:
        with sqlite3.connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, user_id, category, subcategory, colors, source,
                       verification_status, created_at, updated_at
                FROM wardrobe_items
                WHERE user_id = ?
                ORDER BY created_at, id
                """,
                (str(user_id),),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: tuple[object, ...]) -> WardrobeItem:
        (
            item_id,
            user_id,
            category,
            subcategory,
            colors,
            source,
            verification_status,
            created_at,
            updated_at,
        ) = row
        return WardrobeItem(
            id=UUID(str(item_id)),
            user_id=UUID(str(user_id)),
            category=str(category),
            subcategory=str(subcategory) if subcategory is not None else None,
            colors=tuple(json.loads(str(colors))),
            source=str(source),
            verification_status=str(verification_status),
            created_at=datetime.fromisoformat(str(created_at)),
            updated_at=datetime.fromisoformat(str(updated_at)),
        )
