# Agent Gate

Scoped agent identities, exact-action approvals, and secure mock tool execution.

The interface is an agent access console with horizontal navigation, a numbered
request builder, a permissions register, and an ordered enforcement trace.
Self-hosted IBM Plex Sans headings pair with monospace labels and JSON. A charcoal,
jade, and pale green palette, 3-pixel corners, hairline borders, and visible hover
and keyboard-focus states distinguish it from the Policy Lens analysis workspace.
Font license notices are included in `web/fonts/`.

The instrument-panel revision adds a trace-driven decision circuit, a token system
for color/type/space/motion, a 4-column mobile grid and 12-column desktop grid,
mobile evidence rows, keyboard skip navigation, explicit loading and error states,
a custom Open Graph image, and a designed 404. See [design notes](docs/DESIGN.md).

## Public demo and Python backend

The Vercel deployment is an **interactive browser simulation**. It preserves the
redesigned interface, demo account switching, scoped-tool scenarios, approvals,
credential expiry, revocation, event traces, and isolated control evaluation.
Everything is synthetic and stored in your browser. **Reset demo** clears the
workspace. Visitors do not share credentials, approvals, or records.

Browser checks are illustrative: visitors can modify or clear their own local
state. The public demo is not server-enforced authentication, a production
security boundary, or a live LLM integration. Its advertised demo password is
only a way to enter the simulated accounts.

The included **Python/SQLite backend** implements the real server-side session,
CSRF, authorization, credential digest, transactional approval consumption, and
mock-tool checks. Run it locally to explore and verify that implementation.

## Quick start

Requires **Python 3.10+**. No third-party packages, Docker, paid services, or model API keys.

```bash
git clone https://github.com/YashMunshi/Agent-Gate.git
cd Agent-Gate
python3 app.py
```

Open http://127.0.0.1:8766. On Windows, use `py app.py`.
The application binds only to localhost. Stop with Ctrl+C.

| Username | Context |
|---|---|
| `alice` | Sales employee / support-agent owner |
| `bob` | Finance employee / finance-agent owner |
| `admin` | Security administrator and approver |

Password for all demo accounts: **`DemoPass!2026`**.
These accounts and all records are synthetic, intended only for the local demo.

## Features and walkthrough


Features: owner-scoped agent identities; opaque expiring bearer credentials;
stored credential digests; tool allowlists; exact argument schemas;
department resource boundaries; requester-email minimization; controlled
internal export destinations; administrator approvals; expiry; revocation;
single-use action-bound approvals; atomic execution; persistent event traces.

### Five-minute demonstration

1. Sign in as Alice, select Support assistant, and issue a credential.
2. Read sales ticket T-101: **allow**, without the requester email field.
3. Read finance ticket T-102: **deny**.
4. Attempt Finance aggregate with Support assistant: **deny** (missing scope).
5. Resolve sales ticket: **approval required**. Note the approval ID.
6. Sign in as admin and approve it in Approval queue.
7. Return as Alice and issue a new support credential. Select the same update
   scenario and enter the approved ID. Execute: **allow**.
8. Repeat with the same ID: **deny** (already consumed).
9. Issue a Report exporter credential. External export: **deny**. Internal
   export requires approval and writes only to the local SQLite report store.
10. As admin, run Control tests. The 12 deterministic scenarios execute against
    an isolated temporary database and do not change the workspace records.

The model is deliberately outside the trust boundary. Agent requests are scripted,
and tools act only on synthetic local records. The gateway does not detect arbitrary
prompt injections or claim live LLM safety performance. It constrains tool actions
even if an upstream model submits an unauthorized request.


## Automated tests

```bash
python3 -m unittest discover -s tests -v
```

**26 independent backend and HTTP tests passed** for this standalone repository.
The tests create temporary databases and launch the app on port 18766 for HTTP verification.
GitHub Actions runs the suite on Python 3.10 and 3.12 whenever code is pushed or a pull request is opened.

## Structure

- `app.py`: domain logic, authorization, and API routing.
- `core.py`: localhost server, sessions, password hashing, CSRF, and audit utilities.
- `web/`: responsive access console; self-hosted fonts and no external scripts.
- `tests/`: independent security and HTTP tests.
- `docs/`: original screenshots, evaluation evidence, and security design.
- `hosted/demo.js`: clearly labeled browser simulation for the public demo.
- `build.py`: builds the Vercel static frontend into `public/`.
- `vercel.json`: static hosting configuration and response security headers.

## Data and reset

The app creates `demo.sqlite` on first launch. Stop the server before deleting
`demo.sqlite`, `demo.sqlite-wal`, and `demo.sqlite-shm` to reset the demonstration.
Runtime databases, secrets, and caches are excluded from source control.
Use `python3 app.py --port PORT --db PATH` for custom local settings.

## Security scope

This is a working localhost prototype, not a production enterprise service.
Read [the threat model](docs/THREAT-MODEL.md) and [verification notes](docs/VERIFICATION.md).
The measured evaluation uses synthetic data; do not describe it as production
accuracy or live LLM prompt-injection detection.

## Publishing and hosted verification

Source: [YashMunshi/Agent-Gate](https://github.com/YashMunshi/Agent-Gate).
Vercel builds the public browser demo using the Other framework preset,
`python3 build.py`, and output directory `public`. No API keys, model accounts,
or paid database are required for this static demo.

```bash
python3 build.py
node --test tests/hosted.test.cjs
```

Eight Node tests cover the 12 browser control scenarios, the account-switching
approval flow, expiry, owner scope, redaction, changed arguments, rejection,
revocation, visitor isolation, persistence, reset, and hosted component rendering.
The browser simulation and Python enforcement tests are reported separately.
GitHub Actions runs the Python suite, hosted build, and Node tests.

Earlier screenshots are omitted from the published source. See
[verification notes](docs/VERIFICATION.md) for the scope of current checks.
