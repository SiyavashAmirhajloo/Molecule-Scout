We are starting **Version 10 — Production Hardening & Safety**, as
scoped in `docs/roadmap.md`. Versions 0–9 (the complete core product,
including literature structure extraction) are done — review existing
code before proceeding. Re-read the "Responsible Use & Dual-Use Safety
Design" section in `docs/architecture.md` in full — this version makes
that design an enforced part of the running system, not just a doc
section.

## Goal

Harden the product to production shape, and implement the Safety
Agent as real, enforced system behavior.

## Scope for this version only

- **Safety Agent**: structural screening of every generated candidate
  against known toxic-scaffold and controlled-substance structural-
  analog libraries, run as a mandatory step in the LangGraph workflow
  before a candidate can reach the Report Agent or be shown to the
  user. A match must block the candidate, not just flag it. This
  behavior must not be configurable/disableable via settings or
  environment variables — it's a hard product boundary per
  `docs/architecture.md`.
- Confirm and, if needed, reinforce that there is no supported
  generation path conditioned toward maximizing toxicity or any
  chemical-weapons-associated property — audit the Generation Agent's
  exposed parameters and remove or lock down anything that could be
  misused this way.
- Rate limiting on generation requests, per user
- Authentication: JWT, Google OAuth, guest mode (mirroring
  LexBook-AI's approach)
- Structured logging (every generation request logged with its
  requesting project/target, per the logging requirement in
  `docs/architecture.md`), centralized error handling, health/
  readiness checks
- Hardened Docker setup: multi-stage builds, non-root users, proper
  environment/config separation between local/dev/prod
- Job-queue monitoring: queue depth, average latency, and failure rate
  per job type, visible somewhere (even a simple internal endpoint or
  log-based dashboard is fine for this version)
- Deploy pipeline: extend CI to build/push images and, where feasible,
  deploy to a real target

## Ground rules

- This version should not add new generative or scientific
  capabilities — it's entirely about hardening and enforcing safety on
  what already exists from Versions 0–9.
- Ask before adding any new dependency not already listed in
  `docs/tech-stack.md`.
- When done, demonstrate: a login flow including guest mode, a
  generation request that gets rate-limited on repeat, and — most
  importantly — a test case proving the Safety Agent actually blocks a
  flagged structure rather than merely logging a warning about it.
- Summarize what was built and any residual dual-use risk you think is
  still open after this version, even if it's out of scope to fully
  close — flag it rather than implying the product is now risk-free.
