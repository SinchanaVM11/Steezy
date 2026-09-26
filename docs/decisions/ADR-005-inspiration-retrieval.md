# ADR-005: Inspiration image retrieval use-case

## Status

Accepted for the Inspiration → Wardrobe Retrieval milestone.

## Decision

Keep image-query orchestration in a dedicated `InspirationRetrievalService`.
It validates the uploaded image, generates a query vector using the same
embedding provider and metadata contract as indexed wardrobe items, verifies
model/version/source/dimension compatibility, and delegates search to the
existing `RetrievalService`.

The endpoint returns rank, actual cosine score, and embedding provenance. It
does not add recommendation policy, personalization, feedback learning, or
semantic claims.

## Consequences

The flow has one provider contract for indexing and querying, preventing
incomparable vector spaces. Provider mismatch is an explicit client error,
while an empty user wardrobe is a successful empty result. The current
embedding remains a low-level RGB baseline; a future validated fashion model
can replace the provider without changing the use-case or vector repository.
