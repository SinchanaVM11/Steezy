# ADR-004: SQLite vector repository before pgvector

## Status

Accepted for the vector retrieval foundation.

## Decision

Store materialized representation embeddings in a separate
`VectorRepository`. The local implementation serializes vectors as JSON in
SQLite and computes explicit cosine similarity in application code. Search
filters by `user_id` before scoring, applies a caller-provided threshold and
top-k limit, and returns the actual score plus embedding provenance.

The protocol is intentionally compatible with a future PostgreSQL/pgvector
adapter. pgvector is not added now because the repository has no PostgreSQL
runtime, migration system, or production database configuration; introducing
it would create infrastructure without a current deployment target.

## Consequences

The local implementation is durable and testable across repository instances,
but it is not appropriate for large-scale vector search: JSON scans are
linear, similarity is CPU/application computed, and there is no ANN index.
Manual wardrobe items without a representation embedding are excluded from
search. Retrieval semantics are explicitly low-level visual baseline
similarity, not recommendations or semantic fashion relevance.
