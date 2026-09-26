# Retrieval evaluation

## Scope

This document covers the local vector-retrieval foundation only. It does not
evaluate recommendations, personalization, or Inspiration.

The current embedding is `visual-rgb-feature-baseline` version `1`: a
36-dimensional normalized RGB histogram and 2×2 spatial-pool vector. It is a
low-level visual baseline, not semantic fashion similarity.

## Reproducible harness

`backend/tests/test_retrieval.py` is the current deterministic harness. It
uses small generated RGB fixtures and validates:

- cosine identity and orthogonality;
- deterministic ordering, top-k, and threshold behavior;
- strict user isolation;
- empty-index behavior;
- dimension mismatch rejection;
- SQLite persistence across repository instances.

These fixtures are contract fixtures, not a licensed fashion benchmark.
Therefore no Recall@K, Precision@K, MRR, or latency metric is reported.
Generated solid-color images cannot support an honest fashion-quality claim.

## Future benchmark gate

Before selecting a semantic provider or claiming retrieval quality, add a
consented, versioned local benchmark containing same-item/near-item and
non-match pairs across user-upload-like backgrounds. Report Recall@K,
Precision@K, MRR, p50/p95 latency, memory, and artifact size for each exact
model revision and preprocessing configuration. Keep the benchmark outside
the repository if it contains user images, and record only hashes/manifest
metadata here.
