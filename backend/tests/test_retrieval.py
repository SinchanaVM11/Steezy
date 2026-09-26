from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.core.errors import ApiError
from app.models.vector import StoredEmbedding
from app.repositories.vectors import InMemoryVectorRepository, SQLiteVectorRepository, cosine_similarity
from app.repositories.wardrobe import InMemoryWardrobeRepository
from app.schemas.representation import EmbeddingMetadata, VisualEmbedding
from app.services.retrieval import RetrievalService
from app.models.wardrobe import WardrobeItem
from app.api.retrieval import get_retrieval_service
from app.main import app
from fastapi.testclient import TestClient


def item(user_id, item_id=None, representation=None):
    now = datetime.now(timezone.utc)
    return WardrobeItem(
        id=item_id or uuid4(),
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
        representation=representation,
        verified_attributes={},
    )


def representation(values):
    return {
        "visual_embedding": VisualEmbedding(
            values=values,
            metadata=EmbeddingMetadata(
                model_name="test-model",
                model_version="1",
                dimension=len(values),
                source="test",
            ),
        ).model_dump()
    }


def test_cosine_similarity_is_explicit_and_dimension_safe():
    assert cosine_similarity((1.0, 0.0), (1.0, 0.0)) == 1
    assert cosine_similarity((1.0, 0.0), (0.0, 1.0)) == 0
    with pytest.raises(ValueError, match="dimensions"):
        cosine_similarity((1.0,), (1.0, 0.0))


def test_search_is_scoped_sorted_thresholded_and_top_k_limited():
    user_id = uuid4()
    other_user = uuid4()
    wardrobe = InMemoryWardrobeRepository()
    vectors = InMemoryVectorRepository()
    first = item(user_id)
    second = item(user_id)
    foreign = item(other_user)
    for value in (first, second, foreign):
        wardrobe.add(value)
    service = RetrievalService(vectors, wardrobe)
    service.index_item(first.id, user_id, representation([1.0, 0.0]))
    service.index_item(second.id, user_id, representation([0.8, 0.6]))
    service.index_item(foreign.id, other_user, representation([1.0, 0.0]))

    result = service.search(user_id, [1.0, 0.0], top_k=1, threshold=0.7)

    assert len(result.results) == 1
    assert result.results[0].item.id == first.id
    assert result.results[0].retrieval.score == 1
    assert result.semantics == "baseline_low_level_visual_similarity"


def test_empty_index_and_dimension_mismatch_are_safe():
    user_id = uuid4()
    service = RetrievalService(InMemoryVectorRepository(), InMemoryWardrobeRepository())
    assert service.search(user_id, [1.0, 0.0], 10, 0).results == []
    wardrobe = InMemoryWardrobeRepository()
    stored = item(user_id)
    wardrobe.add(stored)
    service = RetrievalService(InMemoryVectorRepository(), wardrobe)
    with pytest.raises(ApiError, match="dimension"):
        service.index_item(stored.id, user_id, {
            "visual_embedding": {
                "values": [1.0],
                "metadata": {"model_name": "x", "model_version": "1", "dimension": 2, "source": "x"},
            }
        })


def test_sqlite_vector_persistence_survives_repository_instance(tmp_path):
    path = str(tmp_path / "vectors.sqlite3")
    embedding = StoredEmbedding(
        wardrobe_item_id=uuid4(),
        user_id=uuid4(),
        values=(1.0, 0.0),
        model_name="model",
        model_version="1",
        dimension=2,
        source="baseline",
        created_at=datetime.now(timezone.utc),
    )
    SQLiteVectorRepository(path).upsert(embedding)
    results = SQLiteVectorRepository(path).search(
        embedding.user_id, (1.0, 0.0), top_k=5, threshold=0.9
    )
    assert results[0][0].wardrobe_item_id == embedding.wardrobe_item_id


def test_search_endpoint_returns_scores_and_enforces_user_scope():
    user_id = uuid4()
    wardrobe = InMemoryWardrobeRepository()
    vectors = InMemoryVectorRepository()
    stored = item(user_id)
    wardrobe.add(stored)
    service = RetrievalService(vectors, wardrobe)
    service.index_item(stored.id, user_id, representation([1.0, 0.0]))
    app.dependency_overrides[get_retrieval_service] = lambda: service
    try:
        response = TestClient(app).post(
            "/wardrobe/search",
            headers={"X-User-ID": str(user_id)},
            json={"embedding": [1.0, 0.0], "top_k": 1, "similarity_threshold": 0.9},
        )
        foreign = TestClient(app).post(
            "/wardrobe/search",
            headers={"X-User-ID": str(uuid4())},
            json={"embedding": [1.0, 0.0]},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["results"][0]["retrieval"]["score"] == 1
    assert foreign.status_code == 200
    assert foreign.json()["results"] == []
