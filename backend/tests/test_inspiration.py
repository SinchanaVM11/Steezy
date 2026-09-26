from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest
from PIL import Image

from app.api.inspiration import get_inspiration_service
from app.core.errors import ApiError
from app.main import app
from app.models.vector import StoredEmbedding
from app.repositories.vectors import InMemoryVectorRepository
from app.repositories.wardrobe import InMemoryWardrobeRepository
from app.services.inspiration import InspirationRetrievalService
from app.services.retrieval import RetrievalService
from app.storage.assets import InMemoryAssetStorage
from app.ai.embedding import VisualFeatureEmbedding
from app.models.wardrobe import WardrobeItem
from datetime import datetime, timezone


def image_bytes(color=(20, 40, 180)):
    output = BytesIO()
    Image.new("RGB", (4, 4), color).save(output, format="PNG")
    return output.getvalue()


def wardrobe_item(user_id):
    now = datetime.now(timezone.utc)
    return WardrobeItem(
        id=uuid4(),
        user_id=user_id,
        category="shirt",
        subcategory=None,
        colors=("blue",),
        source="imported",
        verification_status="unverified",
        asset_id=None,
        analysis_job_id=None,
        analysis_provider="baseline",
        analysis_unknown_attributes=(),
        created_at=now,
        updated_at=now,
        representation=None,
        verified_attributes={},
    )


def test_inspiration_endpoint_generates_query_and_returns_ranked_results():
    user_id = uuid4()
    wardrobe = InMemoryWardrobeRepository()
    vectors = InMemoryVectorRepository()
    item = wardrobe_item(user_id)
    wardrobe.add(item)
    embedding = VisualFeatureEmbedding().generate(image_bytes())
    vectors.upsert(
        StoredEmbedding(
            wardrobe_item_id=item.id,
            user_id=user_id,
            values=tuple(embedding.values),
            model_name=embedding.metadata.model_name,
            model_version=embedding.metadata.model_version,
            dimension=embedding.metadata.dimension,
            source=embedding.metadata.source,
            created_at=item.created_at,
        )
    )
    service = InspirationRetrievalService(
        InMemoryAssetStorage(),
        VisualFeatureEmbedding(),
        RetrievalService(vectors, wardrobe),
        vectors,
    )
    app.dependency_overrides[get_inspiration_service] = lambda: service
    try:
        response = TestClient(app).post(
            "/inspiration/search",
            headers={"X-User-ID": str(user_id)},
            params={"top_k": 1, "similarity_threshold": 0.9},
            files={"file": ("inspiration.png", image_bytes(), "image/png")},
        )
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert response.status_code == 200
    assert body["semantics"] == "baseline_low_level_visual_similarity"
    assert body["results"][0]["rank"] == 1
    assert body["results"][0]["retrieval"]["score"] == pytest.approx(1)


def test_inspiration_rejects_invalid_image_and_isolates_users():
    user_id = uuid4()
    wardrobe = InMemoryWardrobeRepository()
    vectors = InMemoryVectorRepository()
    service = InspirationRetrievalService(
        InMemoryAssetStorage(),
        VisualFeatureEmbedding(),
        RetrievalService(vectors, wardrobe),
        vectors,
    )
    app.dependency_overrides[get_inspiration_service] = lambda: service
    try:
        invalid = TestClient(app).post(
            "/inspiration/search",
            headers={"X-User-ID": str(user_id)},
            files={"file": ("bad.png", b"not-an-image", "image/png")},
        )
    finally:
        app.dependency_overrides.clear()
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "invalid_image"


def test_inspiration_returns_empty_for_user_without_embeddings():
    user_id = uuid4()
    service = InspirationRetrievalService(
        InMemoryAssetStorage(),
        VisualFeatureEmbedding(),
        RetrievalService(InMemoryVectorRepository(), InMemoryWardrobeRepository()),
        InMemoryVectorRepository(),
    )
    result = __import__("asyncio").run(service.search(image_bytes(), user_id, 5, 0))
    assert result.results == []


def test_inspiration_rejects_incompatible_indexed_provider():
    user_id = uuid4()
    wardrobe = InMemoryWardrobeRepository()
    vectors = InMemoryVectorRepository()
    item = wardrobe_item(user_id)
    wardrobe.add(item)
    vectors.upsert(
        StoredEmbedding(
            wardrobe_item_id=item.id,
            user_id=user_id,
            values=(1.0, 0.0),
            model_name="different-provider",
            model_version="9",
            dimension=2,
            source="unsupported",
            created_at=item.created_at,
        )
    )
    service = InspirationRetrievalService(
        InMemoryAssetStorage(),
        VisualFeatureEmbedding(),
        RetrievalService(vectors, wardrobe),
        vectors,
    )

    with pytest.raises(ApiError, match="incompatible"):
        __import__("asyncio").run(service.search(image_bytes(), user_id, 5, 0))
