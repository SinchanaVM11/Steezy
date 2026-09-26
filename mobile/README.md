# Steezy mobile client

This directory contains the first Expo SDK 57 / React Native TypeScript
application shell. It establishes navigation and a typed client for the
backend's `GET /health` contract; it does not implement wardrobe persistence,
image upload, or AI features.

## Setup

```bash
npm install
npm run typecheck
npm test
npm start
```

The shell uses a local backend default of `http://127.0.0.1:8000`. A physical
device cannot reach that loopback address on the development computer; use the
computer's LAN address through a future runtime configuration mechanism rather
than hardcoding it into source code.

## Navigation boundary

- `Home` is the current landing screen and owns the health-contract status
  boundary.
- `Wardrobe` and `Inspiration` are explicit placeholders for later vertical
  slices, not mocked product functionality.
- `src/api/health.tsx` validates the response shape before exposing it to UI
  state.

Planned client responsibilities:

- present API-backed state and empty states;
- upload images through an explicit API contract;
- display actual backend predictions and confidence values;
- collect user verification and feedback.

The mobile client must not contain business logic, fabricated predictions, or
credentials. Navigation is intentionally kept small until the API contracts and
wardrobe domain are defined.
