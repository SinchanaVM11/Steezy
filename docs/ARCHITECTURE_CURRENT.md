# Steezy architecture: current state and phased direction

## Scope of this document

This document records the repository as found at the start of the foundation
phase. The repository contained only
`docs/MASTER_ENGINEERING_SPECIFICATION.txt`; there were no existing screens,
navigation, services, API endpoints, data models, AI modules, or persistence
implementation to retain. The specification is preserved verbatim and remains
the source of truth for the long-term product direction.

## Actual starting state

```text
docs/MASTER_ENGINEERING_SPECIFICATION.txt
```

The foundation adds these executable boundaries:

```text
FastAPI application
  └── GET /health
  └── /wardrobe/items (validated contract, SQLite-backed local persistence)
      └── deterministic metadata analyzer (no image/model/network access)
  └── /feedback (validated, append-only learning signals)
  └── /assets/images (validated bytes → local asset reference)
  └── /analysis/garments (synchronous in-process analysis contract)
      └── /analysis/garments/{job_id}/wardrobe-item (idempotent materialization)
          └── PATCH /wardrobe/items/{item_id}/verification

API errors use a stable envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "correlation_id": "request-uuid",
    "details": []
  }
}
```

The collaboration contract is reproducible with
`python backend/scripts/export_openapi.py`. The script validates the five
current operations and writes a deterministic JSON document without starting a
server or making network calls. Mobile clients should treat this OpenAPI
document as the route/response reference while keeping their runtime API URL
and user ID explicit.

configuration
  └── environment-backed settings (no secrets committed)

Expo SDK 57 mobile application
  ├── native-stack navigation: Home, Wardrobe, Inspiration
  ├── typed health client → GET /health
  └── typed wardrobe state → GET /wardrobe/items?user_id=…
      └── item feedback submission → POST /feedback
```

`GET /health` is a process liveness check. It does not prove database
connectivity, model availability, or application readiness.

## Intended phased architecture

```text
React Native / Expo mobile client
                 │
                 ▼
             FastAPI API
                 │
                 ▼
        application services
          ┌──────┴──────┐
          ▼             ▼
    repositories    AI providers
          │             │
          ▼             ▼
 PostgreSQL/pgvector  perception, attributes,
 object storage       embeddings and retrieval
```

The eventual product flow is:

```text
image → validation → perception → attributes/colors
      → representation/embedding → verified wardrobe data
      → retrieval/recommendation → feedback → profile updates
```

This is a target architecture, not a claim that those components currently
exist.

## Phase plan

### Phase 1 — engineering foundation (complete)

- Establish a small FastAPI application factory and health route.
- Load non-secret runtime settings from environment variables.
- Establish package boundaries for API, services, repositories, schemas, models,
  database, and AI providers.
- Add a focused HTTP test and contributor setup guidance.
- Keep the mobile directory as a documented client boundary.

### Phase 1.5 — mobile application shell (complete)

- Establish an Expo SDK 57 TypeScript application entry point.
- Establish a small native-stack navigation boundary.
- Validate and test the existing backend health response from a typed client.
- Keep Wardrobe and Inspiration as clearly labeled placeholders until their
  backend contracts exist.

### Phase 2 — wardrobe contract and local persistence (complete)

- Define validated wardrobe request/response schemas and domain models.
- Introduce a repository protocol with in-memory and SQLite adapters.
- Expose user-scoped create/list endpoints backed by a local SQLite file.
- Initialize the small schema at repository startup and configure its path with
  `STEEZY_DATABASE_PATH`.
- Add explicit image metadata and privacy/deletion rules.
- Add API contract tests before implementing mobile screens.

### Phase 2.5 — deterministic metadata analysis (current)

- Normalize user-provided garment category and color labels through a dedicated
  analyzer boundary.
- Preserve unknown categories as user input and mark them unknown rather than
  inventing a prediction or confidence score.
- Keep the analyzer replaceable before image-based perception is introduced.

### Phase 2.6 — feedback capture (complete)

- Accept a small allow-list of explicit feedback actions for a wardrobe item.
- Verify the referenced item belongs to the submitting user before recording.
- Persist feedback append-only in SQLite and retain an in-memory adapter for
  isolated tests.
- Do not rank, train, update profiles, or claim that feedback has changed a
  model.

### Phase 2.7 — mobile wardrobe state boundary (current)

- Connect the Expo 57 Wardrobe screen to the existing typed collection API.
- Make loading, empty, success, and API/configuration-error states explicit.
- Keep user identity an explicit runtime configuration value until auth exists.

### Phase 2.8 — mobile feedback interaction (current)

- Submit the six allowed actions (`like`, `dislike`, `save`, `skip`, `wear`,
  `not_relevant`) from each loaded wardrobe item.
- Track submission state per item and prevent duplicate in-flight requests.
- Treat malformed and non-success responses as visible errors; do not claim
  ranking or model learning.

### Phase 2.9 — API observability and error contracts (current)

- Return one JSON error envelope for validation, missing items, ownership
  failures, and persistence failures.
- Attach a safe UUID correlation ID to every response as `X-Request-ID`.
- Parse server messages on mobile while preserving existing loading/success/error
  UI states.

### Phase 3 — fashion perception and representation baseline (complete)

- Validate and preprocess stored image bytes with Pillow.
- Run a replaceable perception boundary that extracts a conservative category
  baseline and dominant RGB-nearest color.
- Generate a deterministic, normalized byte embedding through an
  `EmbeddingService` protocol; this is a seam, not a learned visual model.
- Persist structured predictions, provenance, embedding metadata, asset
  reference, and user-verified attributes separately on wardrobe items.
- Expose an explicit verification endpoint; verification never overwrites AI
  predictions.
- CLIP classification, production garment detection, and vector retrieval are
  intentionally deferred.

### Phase 4 — representation and retrieval

- Add embedding provider abstractions and explicit cosine-similarity retrieval.
- Persist model metadata and vector dimensions.
- Add reproducible experiments, latency measurements, and evaluation docs.

### Phase 5 — context-aware recommendations

- Add context and user-profile services.
- Generate bounded outfit candidates, filter invalid combinations, and rank with
  configurable transparent signals.
- Persist recommendation signals so explanations use actual evidence.

### Phase 6 — mobile client and feedback loop

- Introduce the Expo/TypeScript client as a presentation layer.
- Add wardrobe verification, inspiration, outfit, history, and profile flows
  only as supported by stable API contracts.
- Persist feedback and measure whether personalization improves outcomes.

## Decisions and boundaries

- **No feature simulation:** placeholders must be marked `DEMO`, `MOCK`, or
  `PLACEHOLDER`; the foundation exposes no simulated AI output.
- **No premature database:** PostgreSQL/pgvector is the target persistence
  direction, but no database dependency or schema is introduced until the
  wardrobe contract is defined.
- **Thin API boundary:** route handlers should delegate to services as domain
  behavior is added.
- **Replaceable AI:** model providers will be interfaces/configured adapters,
  not calls embedded throughout route handlers.
- **Privacy by default:** `.env` files, credentials, personal paths, images,
  datasets, and model artifacts are excluded from version control.
- **Scope discipline:** beauty/haircare, social features, chatbot behavior,
  generative try-on, and advanced ranking remain future work as specified.

## Reverse-engineering notes

The current service is intentionally small enough to trace end to end:

1. Uvicorn imports `app.main:app`.
2. `create_app()` constructs the FastAPI application and registers the health
   router.
3. A request to `/health` reaches the route function and returns a typed JSON
   shape.
4. `backend/tests/test_health.py` exercises the public HTTP boundary through
   FastAPI's test client.
5. `core/config.py` demonstrates the future configuration seam without making
   configuration a dependency of the health route yet.
6. `mobile/src/api/health.tsx` normalizes the configured base URL, calls the
   backend health endpoint, and rejects transport or response-contract errors.
7. The wardrobe route depends on a service, the service depends on a repository
   protocol, and the default adapter is SQLite-backed. The in-memory adapter
   remains available for isolated tests and explicit ephemeral use. This allows
   PostgreSQL to replace SQLite without changing the HTTP contract.
8. Wardrobe items intentionally contain user-entered structural fields only.
   AI predictions, confidence, image metadata, and embeddings belong to later
   slices and must not be implied by this API.
9. SQLite initialization creates one wardrobe table and a user-id index. It is
   a local development persistence step, not a production migration system.
   Rows are serialized with standard-library SQLite and JSON; the repository
   reconstructs domain objects before returning them to the service.
10. `DeterministicMetadataAnalyzer` is intentionally not computer vision. It
    receives structured metadata, applies transparent aliases, and returns a
    provider identifier plus unknown attributes. A future image analyzer can
    implement the same `GarmentAnalyzer` protocol without changing the route or
    repository boundaries.
11. Feedback is an event log, not a preference model. The service validates
    ownership, writes one immutable event, and exposes user-scoped reads. The
    action list and raw context are transparent inputs for a future learning
    phase; this implementation performs no learning.
12. `useWardrobe` is the mobile state boundary: it invokes the typed API client,
    maps results into explicit UI states, and preserves prior items on reload
    failure. It does not own authentication, persistence, or business logic.
13. `useFeedback` is a separate item-scoped interaction boundary. Its in-flight
     set prevents duplicate submissions for the same item while allowing
     different items to submit independently. The response is only a stored
     acknowledgement; it does not update recommendations or a model.
14. Error handlers centralize diagnostics without exposing database exception
     text. Clients can show the stable message, while `X-Request-ID` connects a
     report to server logs in a future logging sink.
15. Route decorators declare response models, summaries, tags, and documented
     error statuses. `backend/tests/test_openapi.py` protects stable paths and
     error-schema keys; the export script is the local collaboration artifact,
     not a generated runtime dependency.
16. Asset ingestion deliberately stops at safe byte storage. The generated
     UUID filename prevents user-controlled path traversal; user directories
     provide filesystem isolation, while the returned `storage_key` is an
     internal reference rather than a public path. Future image analysis can
     consume this reference through a separate provider boundary.
17. Garment analysis currently has an explicit job/result shape but executes
     synchronously in-process. It verifies the asset owner, reads stored bytes,
     and sends only filename-derived metadata to the deterministic analyzer.
     `completed` and `failed` are result statuses, not durable queue states;
     missing assets/bytes fail with structured errors and no partial result.
18. Materialization accepts only a completed job from the same in-process
     analysis registry and verifies the request user. The analysis job ID is
     stored with the wardrobe item as the idempotency key; repeated requests
     return the existing item. Asset reference, provider, and unknown attributes
     are retained without adding confidence or inventing predictions.
19. The perception baseline converts stored images to RGB thumbnails before
     extracting one dominant color by nearest reference color. Category uses the
     filename only as an explicitly labeled baseline signal; unsupported
     categories and attributes are `unknown` with null confidence. The
     deterministic byte embedding is normalized and records model name, version,
     dimension, and source, but must not be treated as semantic similarity.
20. `FashionItemRepresentation` stores predicted values and provenance in
     `representation`; `verified_attributes` and `verification_status` are
     separate user-owned state. `PATCH /wardrobe/items/{item_id}/verification`
     is the only current verification write path.

The next implementation should preserve this separation while adding one
vertical slice at a time: define input/output, choose a baseline, implement,
test, evaluate, and document the trade-offs.
