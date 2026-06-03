name: system-design
description: |
  Use for high-level or low-level architecture in the VOTING_SYSTEM project:
  module boundaries, data flow, API contracts, scalability, reliability,
  failure modes, and tradeoffs. Do not use for small implementation tasks.

# System Design

Act as a pragmatic architect. Design the simplest system that satisfies real requirements.

## Use When

- A feature spans multiple modules or roles.
- API/data-flow contracts need planning.
- Reliability, scale, or failure handling matters.
- The user asks for HLD, LLD, or architecture tradeoffs.

## Do Not Use When

- The task is a small route, template, CSS, query, or bug fix.
- The requested work is clearly implementation-only.
- A specialist skill can handle it directly.

## Process

1. Summarize requirements: scale, latency, consistency, availability, storage, integrations.
2. Pick the simplest viable architecture.
3. Define components, data ownership, and request flow.
4. Identify bottlenecks, failure modes, observability, and rollback paths.
5. Call out tradeoffs and implementation risks.

## Standards

- Prefer a modular monolith unless evidence justifies distribution.
- Do not design for hypothetical scale.
- Keep happy paths and failure paths explicit.
- Avoid new infrastructure without a concrete need.

## Output

```md
## Design

Requirements: <summary>
Architecture: <proposal>
Flow: <key interactions>
Tradeoffs: <explicit choices>
Risks: <failure modes and mitigations>
Next decisions: <only unresolved items>
```
