# WCAG Compliance Skill

## Purpose
Ensure the app remains usable for keyboard and assistive technology users while making frontend changes.

## Standards to maintain
- Sufficient color contrast for text and controls.
- Visible keyboard focus states.
- Semantic landmark structure for the page and status regions.
- Data and decisions announced clearly via `aria-live` for dynamic result updates.
- Buttons and actions remain understandable without color alone.

## Checks
- Tab through the interface to verify focus visibility.
- Ensure the decision status area is announced when values change.
- Confirm headings and landmarks remain logical.
- Validate that the main action is clearly labeled.

## Notes
This app is intentionally a simple local-first interface, so accessibility improvements should be lightweight, clear, and maintainable.
