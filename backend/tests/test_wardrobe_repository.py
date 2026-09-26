from uuid import uuid4

from app.repositories.wardrobe import InMemoryWardrobeRepository, SQLiteWardrobeRepository
from app.schemas.wardrobe import WardrobeItemCreate
from app.services.wardrobe import WardrobeService


def test_sqlite_repository_persists_across_instances(tmp_path) -> None:
    database_path = str(tmp_path / "wardrobe.sqlite3")
    user_id = uuid4()
    service = WardrobeService(SQLiteWardrobeRepository(database_path))
    created = service.create_item(
        WardrobeItemCreate(user_id=user_id, category="shirt", colors=["navy"])
    )

    reloaded = WardrobeService(SQLiteWardrobeRepository(database_path))

    assert reloaded.list_items(user_id) == [created]


def test_sqlite_repository_isolates_users(tmp_path) -> None:
    repository = SQLiteWardrobeRepository(str(tmp_path / "wardrobe.sqlite3"))
    service = WardrobeService(repository)
    user_id = uuid4()
    other_user_id = uuid4()
    service.create_item(WardrobeItemCreate(user_id=user_id, category="shirt"))
    service.create_item(WardrobeItemCreate(user_id=other_user_id, category="shoes"))

    assert [item.category for item in service.list_items(user_id)] == ["shirt"]
    assert [item.category for item in service.list_items(other_user_id)] == ["shoes"]


def test_in_memory_repository_remains_available() -> None:
    user_id = uuid4()
    service = WardrobeService(InMemoryWardrobeRepository())

    service.create_item(WardrobeItemCreate(user_id=user_id, category="shirt"))

    assert len(service.list_items(user_id)) == 1
