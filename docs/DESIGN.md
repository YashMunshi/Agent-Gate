# Agent Gate design system

Direction: instrument-panel security console. Structural Plex headings, technical
monospace labels, pale field surfaces, charcoal navigation, and one jade accent.

Audience: recruiters and security engineers evaluating scoped agent access.
Primary action: issue a credential and run a request, then inspect its decision.

## System

CSS custom properties define role-based colors, a 1.25 modular type scale, body
text at 16–18px / 1.6, a 4px-based fixed spacing scale, 3px corners, and 160ms
interaction / 360ms entrance motion. Reduced-motion disables animation.
The mobile grid has four columns; desktop has twelve. Dense evidence tables
reflow to labeled rows below 768px.

The signature decision circuit projects real decision-trace entries into six
named checks. It does not infer missing checks or manufacture evaluation scores.
Blocked, waiting, passed, and not-reached checks have explicit text labels.

## Accessibility and states

The UI includes main/navigation landmarks, one h1, labeled fields, a skip link,
visible keyboard focus, 44px minimum interactive targets, native selects, disabled
execution before credential issuance, inline invalid-JSON feedback, loading copy,
empty states, and a status announcement. API enforcement remains in the Python
backend; the Vercel version is visibly labeled as a public browser simulation.

## Design review

Code-level self-review: hierarchy 4/5, distinctiveness 4/5, readability 4/5,
accessibility 4/5, polish 4/5. These are design judgments, not user research or
performance measurements. Browser verification is reported separately; LCP and
CLS targets have not been measured. Manual acceptance checks: 390px, 768px,
1280px; keyboard-only flow; invalid arguments; approval consumption; 404/share.

## Public entrance revision — October 14, 2026

The security-field-manual entrance replaces the public demo password form,
adds three independently evaluated request specimens, an architecture rail,
scenario-led exploration, evidence links, and direct demo-role entry. The console
gets a demo-perspective selector for completing the approval flow.
Code-level self-review: hierarchy 4/5, distinctiveness 4/5, readability 4/5,
accessibility 4/5, polish 4/5. These are design judgments; browser/viewport and
performance measurements are reported separately and are not implied by them.
