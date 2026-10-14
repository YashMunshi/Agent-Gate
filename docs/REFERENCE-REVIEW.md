# Public reference review — October 14, 2026

Scope: a focused review of public project documentation and product pages.
This is not an exhaustive scrape of every personal project, an endorsement,
or an independent verification of the other projects' security/performance.
No external code, screenshots, logos, benchmarks, or testimonials were copied.

| Public reference | Useful pattern | Application to Agent Gate |
|---|---|---|
| [Thomas-LEON/agentguard](https://github.com/Thomas-LEON/agentguard) | Explicit prototype scope, a layered validation story, and reasoned blocking feedback | Explain what the demo illustrates and expose its actual decision trace. |
| [rigvedrs/agentguard](https://github.com/rigvedrs/agentguard) | Guided onboarding and a concrete description of tool-call validation and tracing | Put an interactive request before the full console and explain its outcome. |
| [Caua-ferraz/AgentGuard](https://github.com/Caua-ferraz/AgentGuard) | Policy decisions, human approvals, and an auditable action lifecycle | Make role switching and the exact-action approval walkthrough easy to follow. |
| [AgentGuard / Lictorate](https://agentguard.lictorate.com/) | A visible request/decision story and a clear enforcement-boundary explanation | Use an interactive specimen plus a readable requester/gateway/tool diagram; no copied metrics or infrastructure claims. |
| [4KInc/agent-authorization-gateway](https://github.com/4KInc/agent-authorization-gateway) | Separating deterministic authorization from the model and presenting decision evidence | Keep the model outside the explanation of authorization and make existing evidence inspectable; no receipt-signing or blockchain claims. |
| [agentgateway](https://agentgateway.dev/) | A gateway positioned through concrete connectivity/security responsibilities | State Agent Gate's narrower purpose and link to source, tests, and the threat model. |

## Implemented direction

Security field manual: a large editorial headline, a functional dark request
specimen, restrained forest/paper colors, a readable architecture rail, deep
scenario rows, and direct technical evidence. The existing console retains its
decision circuit and adds an explicit public-demo role selector.

The preview executes the same browser-demo check code used by the public lab,
with fresh isolated state per request. It never manufactures successful traces,
changes the visitor's lab records, or implies live model calls.

## Deliberate scope

The public demo remains client-controlled and synthetic. The Python/SQLite
backend retains its server-enforced login, ownership, scopes, transactional
approval consumption, and HTTP protections. The new public entrance is not
shipped to replace that backend's authentication page.
