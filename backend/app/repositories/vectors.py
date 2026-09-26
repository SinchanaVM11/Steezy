import json
import math
import sqlite3
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID

from app.core.errors import ApiError
from app.db.sqlite import initialize_database
from app.models.vector import StoredEmbedding


class VectorRepository(Protocol):
    def upsert(self, embedding: StoredEmbedding) -> StoredEmbedding: ...

    def search(
        self, user_id: UUID, query: tuple[float, ...], top_k: int, threshold: float
    ) -> list[tuple[StoredEmbedding, float]]: ...


def cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    if len(left) != len(right):
        raise ValueError("embedding dimensions do not match")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        raise ValueError("embeddings must be non-zero")
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


class InMemoryVectorRepository:
    def __init__(self) -> None:
        self._embeddings: dict[UUID, StoredEmbedding] = {}

    def upsert(self, embedding: StoredEmbedding) -> StoredEmbedding:
        self._embeddings[embedding.wardrobe_item_id] = embedding
        return embedding

    def search(self, user_id, query, top_k, threshold):
        results = []
        for embedding in self._embeddings.values():
            if embedding.user_id != user_id or embedding.dimension != len(query):
                continue
            score = cosine_similarity(embedding.values, query)
            if score >= threshold:
                results.append((embedding, score))
        return sorted(results, key=lambda result: (-result[1], str(result[0].wardrobe_item_id)))[:top_k]


class SQLiteVectorRepository:
    """Local adapter; PostgreSQL/pgvector can implement the same protocol."""

    def __init__(self, database_path: str) -> None:
        self._database_path = database_path
        initialize_database(database_path)

    def upsert(self, embedding: StoredEmbedding) -> StoredEmbedding:
        try:
            with sqlite3.connect(self._database_path) as connection:
                connection.execute(
                    """
                    INSERT INTO wardrobe_embeddings
                    (wardrobe_item_id, user_id, values_json, model_name,
                     model_version, dimension, source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(wardrobe_item_id) DO UPDATE SET
                      user_id=excluded.user_id, values_json=excluded.values_json,
                      model_name=excluded.model_name, model_version=excluded.model_version,
                      dimension=excluded.dimension, source=excluded.source,
                      created_at=excluded.created_at
                    """,
                    (
                        str(embedding.wardrobe_item_id),
                        str(embedding.user_id),
                        json.dumps(embedding.values),
                        embedding.model_name,
                        embedding.model_version,
                        embedding.dimension,
                        embedding.source,
                        embedding.created_at.isoformat(),
                    ),
                )
        except sqlite3.Error as error:
            raise ApiError("persistence_error", "Vector persistence failed.", 503) from error
        return embedding

    def search(self, user_id, query, top_k, threshold):
        with sqlite3.connect(self._database_path) as connection:
            rows = connection.execute(
                """
                SELECT wardrobe_item_id, user_id, values_json, model_name,
                       model_version, dimension, source, created_at
                FROM wardrobe_embeddings
                WHERE user_id = ?
                """,
                (str(user_id),),
            ).fetchall()
        results = []
        for row in rows:
            embedding = StoredEmbedding(
                wardrobe_item_id=UUID(str(row[0])),
                user_id=UUID(str(row[1])),
                values=tuple(json.loads(str(row[2]))),
                model_name=str(row[3]),
                model_version=str(row[4]),
                dimension=int(row[5]),
                source=str(row[6]),
                created_at=datetime.fromisoformat(str(row[7])),
            )
            if embedding.dimension != len(query):
                continue
            score = cosine_similarity(embedding.values, query)
            if score >= threshold:
                results.append((embedding, score))
        return sorted(results, key=lambda result: (-result[1], str(result[0].wardrobe_item_id)))[:top_k]
