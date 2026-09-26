# Steezy

Steezy is a research-oriented fashion intelligence system. Its long-term goal is to turn fashion images and wardrobe data into structured, explainable, personalized recommendations. The repository is currently in the **engineering foundation phase**; advanced computer vision, embeddings, retrieval, and recommendation features are intentionally not implemented yet.

## Repository layout

```text
backend/                  FastAPI service boundary and backend tests
  app/
    api/                  HTTP route modules
    ai/                   Future perception and representation providers
    core/                 Configuration and cross-cutting concerns
    db/                   Future persistence boundary
    models/               Future persistence/domain models
    repositories/         Future data-access implementations
    schemas/              API request/response schemas
    services/             Application/business services
  tests/
mobile/                   Future React Native / Expo client boundary
docs/
  ARCHITECTURE_CURRENT.md Current state and phased target architecture
  MASTER_ENGINEERING_SPECIFICATION.txt Product and engineering specification
```

## Prerequisites

- Python 3.10+
- Node.js 20+ and npm (needed when the Expo client is introduced)

## Backend setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e '.[dev]'
cp .env.example .env
uvicorn app.main:app --app-dir backend --reload
```

The initial service exposes `GET /health` and `GET /docs`. It is a liveness boundary, not an AI or database implementation.

The current HTTP contract can be exported and validated without network access:

```bash
python backend/scripts/export_openapi.py --output /tmp/steezy-openapi.json
```

The generated document describes the health, wardrobe, feedback, and image
asset operations, including successful response models and the shared
structured error envelope.
The Expo client consumes these same route paths through typed clients; its
runtime user ID remains explicit until authentication is added.

Image ingestion currently stores validated JPEG, PNG, or WebP bytes under
`.data/assets` outside SQLite and returns a generated asset reference.

`POST /analysis/garments` is a synchronous, in-process baseline that reads a
user-owned stored asset, preprocesses pixels, extracts low-level RGB features,
and derives the category from the filename baseline. It is not a durable job
queue, CLIP/fashion model, or claim of semantic image understanding.

Run the backend checks with:

```bash
pytest
```

## Mobile status

The `mobile/` directory is a deliberate boundary for the future Expo client. It contains no runnable application yet; the next phase should introduce the client only after the API contract and wardrobe domain have been designed.

## Contribution guidance

1. Read `docs/MASTER_ENGINEERING_SPECIFICATION.txt` and `docs/ARCHITECTURE_CURRENT.md` before making architectural changes.
2. Keep route handlers thin; put business logic in services and data access behind repositories.
3. Keep AI providers replaceable and label mocks/placeholders explicitly.
4. Add focused tests and documentation with each phase.
5. Never commit `.env`, credentials, tokens, user images, datasets, or generated model artifacts.

## Current limitations

There is no authentication, production computer-vision model, or
recommendation engine yet. The current visual feature provider is an offline
evaluated baseline for low-level similarity only; it does not claim semantic
fashion understanding.

The current deterministic metadata analysis is filename/metadata-based and
executes synchronously in-process. A completed analysis can be materialized
with `POST /analysis/garments/{job_id}/wardrobe-item`; the resulting wardrobe
item retains its asset reference, provider, unknown attributes, and analysis
job ID for idempotent retries. Analysis jobs are not durable across process
restarts, and no confidence or computer-vision inference is claimed.

The perception baseline accepts valid stored images, performs RGB thumbnail
preprocessing, extracts a conservative dominant color, and returns a
structured representation with provenance and a normalized image-derived
36-dimensional embedding. User corrections are kept separate via
`PATCH /wardrobe/items/{item_id}/verification`. Export the complete contract
with `python backend/scripts/export_openapi.py --output /tmp/steezy-openapi.json`.

`POST /wardrobe/search` provides user-scoped cosine similarity over
materialized embeddings. Results are explicitly labeled low-level visual
similarity; this is retrieval infrastructure, not recommendations or the
Inspiration feature. See `docs/EVALUATION.md` for the reproducible contract
harness and benchmark limitations.

`POST /inspiration/search` accepts a validated multipart inspiration image,
generates a query embedding with the same baseline provider, and returns
ranked items from the requesting user's wardrobe with actual similarity
scores. The Expo Inspiration screen demonstrates this flow with the SDK 57
image picker. It is not recommendation ranking or semantic fashion reasoning.
