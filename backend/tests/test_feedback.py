from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.repositories.feedback import (
    InMemoryFeedbackRepository,
    SQLiteFeedbackRepository,
)
from app.repositories.wardrobe import SQLiteWardrobeRepository
from app.schemas.feedback import FeedbackCreate
from app.schemas.wardrobe import WardrobeItemCreate
from app.services.feedback import FeedbackService
from app.services.wardrobe import WardrobeService

client = TestClient(app)


def test_feedback_requires_allowed_action() -> None:
    response = client.post(
        "/feedback",
        json={
            "user_id": str(uuid4()),
            "wardrobe_item_id": str(uuid4()),
            "action": "maybe",
        },
    )

    assert response.status_code == 422


def test_feedback_rejects_item_owned_by_another_user() -> None:
    owner_id = uuid4()
    other_user_id = uuid4()
    item_response = client.post(
        "/wardrobe/items",
        json={"user_id": str(owner_id), "category": "shirt"},
    )
    item_id = item_response.json()["id"]

    response = client.post(
        "/feedback",
        json={
            "user_id": str(other_user_id),
            "wardrobe_item_id": item_id,
            "action": "like",
        },
    )

    assert response.status_code == 404


def test_feedback_is_append_only_and_user_scoped(tmp_path) -> None:
    database_path = str(tmp_path / "feedback.sqlite3")
    wardrobe_service = WardrobeService(SQLiteWardrobeRepository(database_path))
    user_id = uuid4()
    other_user_id = uuid4()
    item = wardrobe_service.create_item(
        WardrobeItemCreate(user_id=user_id, category="shirt")
    )
    feedback_service = FeedbackService(
        SQLiteFeedbackRepository(database_path),
        SQLiteWardrobeRepository(database_path),
    )

    recorded = feedback_service.record(
        FeedbackCreate(user_id=user_id, wardrobe_item_id=item.id, action="like")
    )
    feedback_service.record(
        FeedbackCreate(user_id=user_id, wardrobe_item_id=item.id, action="save")
    )

    reloaded = FeedbackService(
        SQLiteFeedbackRepository(database_path),
        SQLiteWardrobeRepository(database_path),
    )
    entries = reloaded.list_for_user(user_id)
    assert entries == [recorded, entries[1]]
    assert reloaded.list_for_user(other_user_id) == []


def test_in_memory_feedback_repository_remains_available() -> None:
    user_id = uuid4()
    item_id = uuid4()
    repository = InMemoryFeedbackRepository()
    feedback_service = FeedbackService(
        repository,
        _WardrobeRepositoryStub(item_id=item_id, user_id=user_id),
    )

    feedback_service.record(
        FeedbackCreate(
            user_id=user_id,
            wardrobe_item_id=item_id,
            action="skip",
        )
    )

    assert len(feedback_service.list_for_user(user_id)) == 1


class _WardrobeRepositoryStub:
    def __init__(self, item_id, user_id) -> None:
        self.item_id = item_id
        self.user_id = user_id

    def get_for_user(self, item_id, user_id):
        return object() if item_id == self.item_id and user_id == self.user_id else None
