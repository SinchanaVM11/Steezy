# ADR-003: Evaluated local model-provider upgrade

## Status

Superseded as the default-provider decision by the audit in
`docs/evaluations/MODEL_PROVIDER_EVALUATION.md`. The implementation remains
the safe repository baseline while pretrained candidates are evaluated.

## Audit

The existing perception implementation performs RGB conversion, a simple
dominant-color estimate, and filename-derived category normalization. Its
`deterministic-byte-baseline` embedding is repeatable but unrelated to image
content: changing pixels can change the hash arbitrarily, and similar images
have no reason to be nearby. There are no cached pretrained weights in the
development environment.

## Previous decision

Replace the hash embedding as the default with a deterministic
`VisualFeatureEmbedding` provider. It represents the actual image using
normalized RGB histograms plus spatially pooled RGB values, and records a
stable model name, version, dimension, and source. This is meaningful for
low-level visual similarity (especially color/layout), but is not semantic
fashion understanding.

Keep garment category perception explicitly labeled as the
`filename-category-baseline`. Its evaluation checks contract behavior and
unknown handling; it does not claim visual garment detection or confidence.
The `EmbeddingService` and `PerceptionService` protocols remain the
replacement seams for a pretrained CLIP or fashion-specific provider.

## Evaluation gate

The checked-in evaluation fixtures verify deterministic output, unit
normalization, same-image identity, sensitivity to materially different image
colors, stable dimensionality, provenance, and explicit unknown outputs. This
is a provider regression gate, not a model-quality benchmark. A future
pretrained provider must add a labeled image set, accuracy/retrieval metrics,
model artifact/version pinning, and a reproducible offline evaluation command
before becoming the default.

## Consequences

The default pipeline remains offline and has no secret or download requirement,
but the embedding is still not suitable for semantic retrieval. Vector
storage and Inspiration remain deferred. The follow-up audit recommends
FashionCLIP 2.0 as the next experiment, not as a shipped default.
