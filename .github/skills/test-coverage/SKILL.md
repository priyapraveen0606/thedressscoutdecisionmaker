# Test Coverage Skill

## Purpose
Validate the style decision engine and ensure frontend changes do not regress core business logic.

## Commands
- Backend regression tests:
  `cd /workspaces/thedressscoutdecisionmaker && python3 -m pytest backend/tests/test_anchor_rules.py -q`
- Optional frontend smoke check:
  `cd /workspaces/thedressscoutdecisionmaker/frontend && npm run build`

## Expected outcome
- Decision logic still returns BUY / ALTER_THEN_BUY / PASS as expected.
- Rule changes remain consistent with the local private profile.
- Frontend UX remains stable and accessible.

## Notes
This project does not need a broad user-management test suite yet; the priority is verifying the anchored style engine and local app behavior.
