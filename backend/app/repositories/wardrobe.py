import json
import sqlite3
from collections.abc import Iterable
from dataclasses import replace
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID

from app.models.wardrobe import WardrobeItem
from app.db.sqlite import initialize_database
from app.core.errors import ApiError


class WardrobeRepository(Protocol):
    def add(self, item: WardrobeItem) -> WardrobeItem: ...

    def get(self, item_id: UUID) -> WardrobeItem | None: ...

    def get_for_user(self, item_id: UUID, user_id: UUID) -> WardrobeItem | None: ...

    def get_by_analysis_job_for_user(
        self, analysis_job_id: UUID, user_id: UUID
    ) -> WardrobeItem | None: ...

    def list_for_user(self, user_id: UUID) -> Iterable[WardrobeItem]: ...

    def update_verification(
        self, item_id: UUID, user_id: UUID, attributes: dict[str, str]
    ) -> WardrobeItem | None: ...


class InMemoryWardrobeRepository:
    """Development adapter; data is lost when the API process stops."""

    def __init__(self) -> None:
        self._items: dict[UUID, WardrobeItem] = {}

    def add(self, item: WardrobeItem) -> WardrobeItem:
        self._items[item.id] = item
        return item

    def get(self, item_id: UUID) -> WardrobeItem | None:
        return self._items.get(item_id)

    def list_for_user(self, user_id: UUID) -> list[WardrobeItem]:
        return [item for item in self._items.values() if item.user_id == user_id]

    def get_for_user(self, item_id: UUID, user_id: UUID) -> WardrobeItem | None:
        item = self._items.get(item_id)
        return item if item is not None and item.user_id == user_id else None

    def get_by_analysis_job_for_user(
        self, analysis_job_id: UUID, user_id: UUID
    ) -> WardrobeItem | None:
        return next(
            (
                item
                for item in self._items.values()
                if item.analysis_job_id == analysis_job_id and item.user_id == user_id
            ),
            None,
        )

    def update_verification(self, item_id, user_id, attributes):
        item = self.get_for_user(item_id, user_id)
        if item is None:
            return None
        updated = replace(
            item,
            verification_status="verified",
            verified_attributes=attributes,
            updated_at=datetime.now(timezone.utc),
        )
        self._items[item_id] = updated
        return updated


class SQLiteWardrobeRepository:
    """Durable local adapter; PostgreSQL can replace it behind the same protocol."""

    def __init__(self, database_path: str) -> None:
        self._database_path = database_path
        initialize_database(database_path)

    def add(self, item: WardrobeItem) -> WardrobeItem:
        try:
            with sqlite3.connect(self._database_path) as connection:
                connection.execute(
                """
                INSERT INTO wardrobe_items
                (id, user_id, category, subcategory, colors, source,
                 verification_status, asset_id, analysis_job_id, analysis_provider,
                 analysis_unknown_attributes, created_at, updated_at,
                 representation, verified_attributes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                    str(item.id),
                    str(item.user_id),
                    item.category,
                    item.subcategory,
                    json.dumps(item.colors),
                    item.source,
                    item.verification_status,
                    str(item.asset_id) if item.asset_id else None,
                    str(item.analysis_job_id) if item.analysis_job_id else None,
                    item.analysis_provider,
                    json.dumps(item.analysis_unknown_attributes),
                    item.created_at.isoformat(),
                    item.updated_at.isoformat(),
                    json.dumps(item.representation) if item.representation else None,
                    json.dumps(item.verified_attributes or {}),
                    ),
                )
        except sqlite3.Error as error:
            raise ApiError("persistence_error", "Wardrobe persistence failed.", 503) from error
        return item

    def list_for_user(self, user_id: UUID) -> list[WardrobeItem]:
        with sqlite3.connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, user_id, category, subcategory, colors, source,
                       verification_status, asset_id, analysis_job_id, analysis_provider,
                       analysis_unknown_attributes, created_at, updated_at,
                       representation, verified_attributes
                FROM wardrobe_items
                WHERE user_id = ?
                ORDER BY created_at, id
                """,
                (str(user_id),),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def get(self, item_id: UUID) -> WardrobeItem | None:
        with sqlite3.connect(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT id, user_id, category, subcategory, colors, source,
                       verification_status, asset_id, analysis_job_id, analysis_provider,
                       analysis_unknown_attributes, created_at, updated_at,
                       representation, verified_attributes
                FROM wardrobe_items
                WHERE id = ?
                """,
                (str(item_id),),
            ).fetchone()
        return self._from_row(row) if row is not None else None

    def get_for_user(self, item_id: UUID, user_id: UUID) -> WardrobeItem | None:
        with sqlite3.connect(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT id, user_id, category, subcategory, colors, source,
                       verification_status, asset_id, analysis_job_id, analysis_provider,
                       analysis_unknown_attributes, created_at, updated_at,
                       representation, verified_attributes
                FROM wardrobe_items
                WHERE id = ? AND user_id = ?
                """,
                (str(item_id), str(user_id)),
            ).fetchone()
        return self._from_row(row) if row is not None else None

    def get_by_analysis_job_for_user(
        self, analysis_job_id: UUID, user_id: UUID
    ) -> WardrobeItem | None:
        with sqlite3.connect(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT id, user_id, category, subcategory, colors, source,
                       verification_status, asset_id, analysis_job_id, analysis_provider,
                       analysis_unknown_attributes, created_at, updated_at,
                       representation, verified_attributes
                FROM wardrobe_items
                WHERE analysis_job_id = ? AND user_id = ?
                """,
                (str(analysis_job_id), str(user_id)),
            ).fetchone()
        return self._from_row(row) if row is not None else None

    def update_verification(self, item_id, user_id, attributes):
        with sqlite3.connect(self._database_path) as connection:
            cursor = connection.execute(
                """
                UPDATE wardrobe_items
                SET verification_status = 'verified',
                    verified_attributes = ?,
                    updated_at = ?
                WHERE id = ? AND user_id = ?
                """,
                (
                    json.dumps(attributes),
                    datetime.now(timezone.utc).isoformat(),
                    str(item_id),
                    str(user_id),
                ),
            )
            if cursor.rowcount == 0:
                return None
        return self.get_for_user(item_id, user_id)

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
            asset_id,
            analysis_job_id,
            analysis_provider,
            analysis_unknown_attributes,
            created_at,
            updated_at,
            representation,
            verified_attributes,
        ) = row
        return WardrobeItem(
            id=UUID(str(item_id)),
            user_id=UUID(str(user_id)),
            category=str(category),
            subcategory=str(subcategory) if subcategory is not None else None,
            colors=tuple(json.loads(str(colors))),
            source=str(source),
            verification_status=str(verification_status),
            asset_id=UUID(str(asset_id)) if asset_id else None,
            analysis_job_id=UUID(str(analysis_job_id)) if analysis_job_id else None,
            analysis_provider=str(analysis_provider) if analysis_provider else None,
            analysis_unknown_attributes=tuple(json.loads(str(analysis_unknown_attributes))),
            created_at=datetime.fromisoformat(str(created_at)),
            updated_at=datetime.fromisoformat(str(updated_at)),
            representation=json.loads(str(representation)) if representation else None,
            verified_attributes=json.loads(str(verified_attributes or "{}")),
        )
