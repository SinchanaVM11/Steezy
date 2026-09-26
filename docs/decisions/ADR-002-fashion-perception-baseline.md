# ADR-002: Replaceable fashion perception baseline

## Status

Accepted for the first Fashion Perception + Representation milestone.

## Decision

Use a small, synchronous perception service over already-stored image bytes.
The service performs RGB conversion and thumbnail preprocessing, extracts one
dominant color using nearest reference colors, keeps filename-derived category
classification explicitly labeled as a baseline, and emits `unknown` with
`null` confidence when the implementation cannot infer an attribute.

Embedding generation is behind an `EmbeddingService` protocol. The current
implementation is a deterministic SHA-256-derived normalized vector with
explicit model name, version, dimension, and source metadata. It is a
repeatable contract fixture, not a CLIP or production visual embedding.

Predictions are persisted inside `FashionItemRepresentation`; user corrections
are persisted separately in `verified_attributes` and are applied through the
verification endpoint.

## Alternatives considered

- **CLIP or another pretrained model now:** rejected because it would add
  heavyweight downloads, runtime variability, and unsupported confidence claims
  before an evaluation dataset and model-serving boundary exist.
- **Vector search now:** rejected; the representation records embedding
  metadata, while retrieval belongs to the next milestone.
- **Store user verification over predictions:** rejected because it destroys
  provenance and prevents later comparison of model output with corrections.

## Consequences

The pipeline is testable without network access or secrets and can be replaced
by a real perception or embedding provider without changing the API boundary.
The current category and embedding signals are not suitable for production
recommendations, similarity search, or quality claims.
