from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_and_list_wardrobe_items() -> None:
    user_id = uuid4()
    response = client.post(
        "/wardrobe/items",
        json={
            "user_id": str(user_id),
            "category": "shirt",
            "colors": ["navy", "white"],
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["user_id"] == str(user_id)
    assert created["verification_status"] == "unverified"
    assert created["source"] == "user"
    assert client.get(f"/wardrobe/items?user_id={user_id}").json() == [created]


def test_create_wardrobe_item_rejects_invalid_category() -> None:
    response = client.post(
        "/wardrobe/items",
        json={"user_id": str(uuid4()), "category": ""},
    )

    assert response.status_code == 422


def test_list_wardrobe_items_is_scoped_to_user() -> None:
    user_id = uuid4()
    other_user_id = uuid4()
    client.post(
        "/wardrobe/items",
        json={"user_id": str(user_id), "category": "trousers"},
    )
    client.post(
        "/wardrobe/items",
        json={"user_id": str(other_user_id), "category": "shoes"},
    )

    items = client.get(f"/wardrobe/items?user_id={user_id}").json()

    assert len(items) == 1
    assert items[0]["category"] == "trousers"
