import sqlite3
from collections.abc import Iterable
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.db.sqlite import initialize_database
from app.models.feedback import Feedback


class FeedbackRepository(Protocol):
    def add(self, feedback: Feedback) -> Feedback: ...

    def list_for_user(self, user_id: UUID) -> Iterable[Feedback]: ...


class InMemoryFeedbackRepository:
    def __init__(self) -> None:
        self._feedback: list[Feedback] = []

    def add(self, feedback: Feedback) -> Feedback:
        self._feedback.append(feedback)
        return feedback

    def list_for_user(self, user_id: UUID) -> list[Feedback]:
        return [entry for entry in self._feedback if entry.user_id == user_id]


class SQLiteFeedbackRepository:
    """Durable append-only local adapter for feedback events."""

    def __init__(self, database_path: str) -> None:
        self._database_path = database_path
        initialize_database(database_path)

    def add(self, feedback: Feedback) -> Feedback:
        with sqlite3.connect(self._database_path) as connection:
            connection.execute(
                """
                INSERT INTO feedback
                (id, user_id, wardrobe_item_id, action, context, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(feedback.id),
                    str(feedback.user_id),
                    str(feedback.wardrobe_item_id),
                    feedback.action,
                    feedback.context,
                    feedback.created_at.isoformat(),
                ),
            )
        return feedback

    def list_for_user(self, user_id: UUID) -> list[Feedback]:
        with sqlite3.connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, user_id, wardrobe_item_id, action, context, created_at
                FROM feedback
                WHERE user_id = ?
                ORDER BY created_at, id
                """,
                (str(user_id),),
            ).fetchall()
        return [
            Feedback(
                id=UUID(str(row[0])),
                user_id=UUID(str(row[1])),
                wardrobe_item_id=UUID(str(row[2])),
                action=str(row[3]),
                context=str(row[4]) if row[4] is not None else None,
                created_at=datetime.fromisoformat(str(row[5])),
            )
            for row in rows
        ]
