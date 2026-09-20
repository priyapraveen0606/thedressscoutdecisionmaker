# Petite Office Agent

A local-first style decision engine for office-dress recommendations.

## Purpose

- Evaluate product fit with a private, encrypted personal anchor profile
- Apply business rules for sleeve requirement, silhouette, hem length, color palette, and formality
- Return BUY / ALTER_THEN_BUY / PASS decisions
- Keep private profile values out of source files and away from the browser
- Support a future parameterized multi-user architecture without committing prematurely

## Current architecture

- Backend: FastAPI service with deterministic evaluation rules
- Frontend: Vite + React local UI for profile editing and evaluation
- Storage: encrypted local profile persisted in `.env` using Fernet
- AI layer: optional, backend-only, and gracefully falls back if unavailable or invalid

## Security model

This project is intentionally local-first and single-user today:

- the personal profile is encrypted and stored locally
- no profile data is committed to source control
- the admin profile path is a local management seam for future parameterization
- no API keys or private profile details are exposed to the frontend

## Local setup

1. Make sure the project dependencies are installed:
   - `cd /workspaces/thedressscoutdecisionmaker && python3 -m pip install -r requirements.txt`
   - `cd /workspaces/thedressscoutdecisionmaker/frontend && npm install`
2. Create or update `.env` with your encrypted profile values.
3. Start the backend:
   - `cd /workspaces/thedressscoutdecisionmaker && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`
4. Start the frontend:
   - `cd /workspaces/thedressscoutdecisionmaker/frontend && npm run dev -- --host 0.0.0.0`
5. Open the frontend locally and use the profile editor to save the encrypted profile.

## One-command local run

If you want to start the services together for local validation:

```bash
cd /workspaces/thedressscoutdecisionmaker && (uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 & cd frontend && npm run dev -- --host 0.0.0.0)
```

This starts the API and Vite dev server in one shell session for local testing.

## Encrypted profile setup

The app expects values like these in `.env`:

```bash
PERSONAL_PROFILE_SECRET="<fernet-secret>"
PERSONAL_PROFILE_ENCRYPTED="<encrypted-json>"
```

The helper script can generate the encrypted payload:

```bash
cd /workspaces/thedressscoutdecisionmaker && python3 scripts/create_profile.py
```

## Local validation commands

### Backend tests

```bash
cd /workspaces/thedressscoutdecisionmaker && /usr/bin/python3.12 -m pytest backend/tests/test_anchor_rules.py -q
```

### Frontend build

```bash
cd /workspaces/thedressscoutdecisionmaker/frontend && npm run build
```

### Production-style smoke test with dummy AI key

```bash
cd /workspaces/thedressscoutdecisionmaker && OPENAI_API_KEY=dummy-key uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Then test the endpoints:

- `/health`
- `/profile`
- `/ai/search-queries`
- `/search/evaluate`

## Expected behavior

- The local encrypted profile loads correctly.
- Search queries are generated from the private profile.
- The curated evaluation returns BUY / ALTER_THEN_BUY / PASS items.
- If the OpenAI key is missing or invalid, the app still runs and falls back to deterministic local scoring.

## Notes

This app purposely keeps a private single-user workflow today while exposing a profile management seam for future parameterization. It is not yet a public multi-user admin system, but the structure is ready to evolve without reworking the core rules.
