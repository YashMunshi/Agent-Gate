# Agent Gate — Security design

This repository is self-contained. The design notes below document the shared
controls and compare it with its companion prototype for context.


## System boundary

Both applications are localhost learning prototypes with fictional Northstar
enterprise data. Browser input is untrusted. User identity and role come from
server-side session records. The database, backend source, and local computer
are trusted. A person who controls these can change the demo and is out of scope.

Access Atlas's device and risk fields are deliberately simulated. They are not
trusted attestation. Authentication is local account authentication, not SSO,
OIDC, WebAuthn, or real MFA. Agent Gate implements capability-limited service
identities, not cloud workload federation.

## Assets

- Synthetic department records and local mock ticket state.
- Policy versions and temporary access decisions.
- Session tokens, agent credentials, and CSRF secrets.
- Approval integrity and one-time execution.
- Audit events and evaluation evidence.

## Trust boundaries

Browser → localhost HTTP handler → identity validation → authorization → SQLite.
For agent execution: caller → bearer credential → tool scope → argument schema →
resource boundary → action-bound approval → mock tool side effect.

## Threats and controls

| Threat | Implemented control | Verification |
|---|---|---|
| Forged user role in request | Role loaded from server session and users table | HTTP forged-role test |
| Cross-department access | Server-side department checks | Both projects' boundary tests |
| UI bypass | Checks also run on direct API requests | HTTP bearer and access tests |
| CSRF / cross-origin calls | SameSite cookies, CSRF header, Origin and Host validation | HTTP CSRF and origin tests |
| Password brute force | PBKDF2 hashing and per-username throttling | Persistent limiter test |
| Secret disclosure | HttpOnly cookies; agent secrets stored only as digests; no bearer logs | Token digest test |
| Persistent excess privilege | Temporary grants and credentials expire and can be revoked | Expiry/revocation tests |
| Agent requests forbidden tool | Scope allowlist at execution boundary | Out-of-scope tool tests |
| Unexpected tool parameters | Exact schema field sets and value restrictions | Unexpected argument test |
| Sensitive fields in output | Explicit response field selection | Email-exclusion test |
| External export | Destination must be internal://reports; no network export occurs | External destination denial |
| Approval applied to changed request | Fingerprint binds agent, tool, and canonical arguments; requester also checked | Changed-arguments test |
| Approval replay or race | BEGIN IMMEDIATE transaction encloses consumption and mock side effect | Concurrent consumption test |
| Privilege changed after approval | Recheck credential and policy before side effect | Revocation test |
| Self approval | Approver must be admin and differ from requester | Self-approval tests |
| SQL injection | Parameterized queries | Code review; inputs treated as data |
| Script injection in visible data | Escaped text and restricted CSP | UI uses escaping; no inline scripts |

## Important limitations

- Python's built-in HTTP server is appropriate for this local demo, not public
  production hosting. HTTP cookies lack Secure because localhost is HTTP.
- Demo users and passwords are public. There is no MFA, real identity provider,
  account recovery, or user provisioning.
- The login limiter is per username, not a complete distributed anti-abuse system.
- Audit records are persistent but not immutable or cryptographically tamper-evident.
- Access Atlas returns synthetic exports as JSON; it does not control downstream
  handling by an authorized human who has already received records.
- Agent Gate uses fixed scopes and mock tools. No filesystem, shell, network
  browsing, external email, real payments, or production database tools execute.
- It does not claim a general solution to prompt injection; permissions limit the
  consequences of unauthorized tool requests, but authorized malicious behavior
  can require further contextual controls.
- The stored evaluation sample is synthetic. Labels derive from a documented
  fictional policy, not independent enterprise incident adjudication.
- SQLite serializes writes; sustained enterprise performance is not benchmarked.
- Approval execution is transactional only because the side effects are local
  SQLite writes. External services would require idempotency and durable coordination.

## Before a public deployment

Replace demo credentials and authentication with a real identity provider; add TLS,
Secure cookies, secret management, trusted posture/risk sources, centralized access
policy distribution, protected audit retention, operational rate limits, request
timeouts, monitoring, and dependency/runtime maintenance. Move to a supported
production server and review policy/approval behavior under real workloads.
Retain a strict synthetic-data boundary for any publicly shareable portfolio demo.

## Hosted browser simulation

The Vercel build is a public, browser-local simulation. Its demo account selection,
credentials, approvals, and audit records are client-controlled. They are not
trusted security evidence and do not provide production authentication or
server-enforced authorization. The Python backend described above is retained
for local enforcement and independent backend verification.
