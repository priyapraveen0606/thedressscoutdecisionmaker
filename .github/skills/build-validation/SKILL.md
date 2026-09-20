# Build Validation Skill

## Purpose
Verify that the app remains buildable and that frontend changes do not break the local run experience.

## Required checks
1. Run backend tests.
2. Run the frontend production build.
3. Confirm the app still renders the core evaluation workflow.

## Commands
- Backend tests:
  `cd /workspaces/thedressscoutdecisionmaker && python3 -m pytest backend/tests/test_anchor_rules.py -q`
- Frontend build:
  `cd /workspaces/thedressscoutdecisionmaker/frontend && npm run build`

## Pass criteria
- Tests pass.
- Frontend build exits successfully.
- No accessible-name or keyboard-focus regressions are introduced.
- The app continues to work with encrypted local profile configuration.
