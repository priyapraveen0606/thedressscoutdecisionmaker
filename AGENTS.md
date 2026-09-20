# AGENTS.md

## Project overview
This repository contains a local-first personal style decision app for office-dress recommendations. The app intentionally keeps a private profile outside source control using encrypted environment configuration and expose a profile admin endpoint.

## Core principles
- Keep the personal profile encrypted and local by default.
- Provide a local admin profile management endpoint for editing the active profile without exposing it publicly.
- Prefer a parameterizable architecture for future multi-user support instead of creating a user management layer prematurely.
- Validate backend rules before frontend UI changes.
- Maintain accessibility and usability in all front-end updates.

## Local workflow
1. Backend: run the Python app with uvicorn.
2. Frontend: run Vite in the frontend folder.
3. Verify backend logic with pytest before finalizing UI or rule changes.
4. Test the frontend build with npm run build after frontend edits.

## Commands
- Backend: `cd /workspaces/thedressscoutdecisionmaker && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`
- Frontend: `cd /workspaces/thedressscoutdecisionmaker/frontend && npm install && npm run dev -- --host 0.0.0.0`
- Tests: `cd /workspaces/thedressscoutdecisionmaker && python3 -m pytest backend/tests/test_anchor_rules.py -q`
- Frontend build: `cd /workspaces/thedressscoutdecisionmaker/frontend && npm run build`

## Required checks before completion
- Backend tests pass.
- Frontend build succeeds.
- UI updates keep keyboard focus visibility and semantic structure accessible.
- Local profile management remains encrypted and never stored in source code.

## Local testing note
This app is designed for a local single-user workflow today, with a basic admin profile endpoint for profile edits. It is intentionally not yet a public multi-user admin system, but the local admin route creates the needed management seam for future parameterization.
