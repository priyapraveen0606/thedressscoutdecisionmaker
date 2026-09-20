# Agent Testing Guide

This document is for local validation and regression checks when changing the app.

## Required workflow

1. Validate backend tests:
   - `cd /workspaces/thedressscoutdecisionmaker && /usr/bin/python3.12 -m pytest backend/tests/test_anchor_rules.py -q`
2. Validate frontend build:
   - `cd /workspaces/thedressscoutdecisionmaker/frontend && npm run build`
3. Validate the app with a dummy API key:
   - `cd /workspaces/thedressscoutdecisionmaker && OPENAI_API_KEY=dummy-key uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`
4. Exercise the live API:
   - `/health`
   - `/profile`
   - `/ai/search-queries`
   - `/search/evaluate`

## What to expect

- The app should return `200` for health and profile calls.
- The local encrypted profile should load successfully from `.env`.
- Search query generation should use the profile and return retailer-specific queries.
- The search/evaluate endpoint should return a curated list even when `OPENAI_API_KEY` is a dummy value.
- The app should degrade gracefully and use the deterministic local summary if the AI service is unavailable or invalid.

## Security expectation

- No private profile details should appear in source files.
- No API keys should be logged to the terminal or frontend.
- The AI layer remains server-side only.

## Production-readiness note

The app is still intentionally designed as a local-first single-user workflow. The admin profile path exists as a local management seam for future parameterization, but it is not a public multi-user admin system.
