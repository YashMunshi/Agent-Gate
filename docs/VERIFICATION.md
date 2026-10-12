# Agent Gate verification

## Current UI refactor — October 11, 2026 (UTC)

The console uses structural sans headings and monospace metadata, horizontal
navigation, a compact status strip, an asymmetric request-builder / permissions
layout, and a unified 3-pixel border radius. Static font assets are served through
an explicit allowlist with `font/woff` content type. No authorization, approval,
credential, tool execution, or persistence rules were changed.

Verification includes the 26 existing backend and HTTP tests, JavaScript syntax,
rendering every tab for Alice, Bob, and Admin with real synthetic state, and HTML
checks for unique IDs and associated form labels. All three font assets returned
HTTP 200 with the correct MIME type and exact file bytes; unlisted font paths and
a traversal path returned 404. Current browser visual and
interaction testing was unavailable in the editing environment. Responsive rules
are implemented but have not been visually verified in a browser for this revision.

Run `python3 -m unittest discover -s tests -v` to reproduce the backend suite.

## Earlier baseline

The original implementation passed Chromium workflows covering login, access
decisions, approval flows, evaluation, and independent sessions. Earlier screenshots predate this redesign and are omitted from the published source.

Evaluation evidence is in the included JSON file. Data and labels are synthetic.
Decision latency varies by computer; no production accuracy is claimed.

## Public browser demo

The Vercel static build has eight passing Node tests covering all 12 isolated
control scenarios, account switching, approvals, expiry, redaction, revocation,
visitor isolation, reset, and rendering each tab. This verifies a browser
simulation, not server-enforced security. No live LLM is used.

## Instrument-panel design revision — October 12, 2026 UTC

All 26 backend tests and 8 hosted tests passed. Token contrast pairs measure
5.27:1 or higher for body/muted/status text. A real HTTP check verified the PNG
share asset and the designed HTML 404 response. Browser rendering and exact
390/768/1280px viewport verification remain pending dashboard access.
