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

configuration
  └── environment-backed settings (no secrets committed)

Expo SDK 57 mobile application
  ├── native-stack navigation: Home, Wardrobe, Inspiration
  └── typed health client → GET /health
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

### Phase 1.5 — mobile application shell (current)

- Establish an Expo SDK 57 TypeScript application entry point.
- Establish a small native-stack navigation boundary.
- Validate and test the existing backend health response from a typed client.
- Keep Wardrobe and Inspiration as clearly labeled placeholders until their
  backend contracts exist.

### Phase 2 — wardrobe contract and persistence

- Define validated wardrobe request/response schemas and domain models.
- Introduce PostgreSQL migrations and repository interfaces.
- Add explicit image metadata and privacy/deletion rules.
- Add API contract tests before implementing mobile screens.

### Phase 3 — fashion perception baseline

- Add image validation and a replaceable perception provider.
- Keep predicted values, confidence, model name, and version separate from
  user-verified attributes.
- Evaluate category and color baselines on documented data; never fabricate
  confidence or metrics.

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

The next implementation should preserve this separation while adding one
vertical slice at a time: define input/output, choose a baseline, implement,
test, evaluate, and document the trade-offs.
