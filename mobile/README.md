# Steezy mobile client

This directory is the reserved boundary for the React Native / Expo TypeScript
client described in the engineering specification. The client is intentionally
not runnable in the foundation phase. The next phase should establish the API
contract and wardrobe domain before introducing navigation or screens.

Planned client responsibilities:

- present API-backed state and empty states;
- upload images through an explicit API contract;
- display actual backend predictions and confidence values;
- collect user verification and feedback.

The mobile client must not contain business logic, fabricated predictions, or
credentials.
