# Local Testing Skill

## Purpose
Run and validate the app in a local dev environment without introducing a profile admin surface.

## Setup
1. Ensure the project dependencies are installed.
2. Create or confirm a valid `.env` file with `PERSONAL_PROFILE_SECRET` and `PERSONAL_PROFILE_ENCRYPTED`.
3. Keep the app local-first: no user management endpoints are required for this phase.

## Commands
- Backend:
  `cd /workspaces/thedressscoutdecisionmaker && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`
- Frontend:
  `cd /workspaces/thedressscoutdecisionmaker/frontend && npm install && npm run dev -- --host 0.0.0.0`
- Backend test:
  `cd /workspaces/thedressscoutdecisionmaker && python3 -m pytest backend/tests/test_anchor_rules.py -q`
- Frontend production build:
  `cd /workspaces/thedressscoutdecisionmaker/frontend && npm run build`

## Validation checklist
- The backend server responds on port 8000.
- The frontend renders the app and loads the profile from the backend.
- The evaluation request returns BUY / ALTER_THEN_BUY / PASS successfully.
- The app remains accessible for keyboard and screen-reader users.

## Notes
Use this skill when validating local behavior before shipping or expanding the app to broader user flows.
