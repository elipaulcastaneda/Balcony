Copilot instructions for this repository
=====================================

This repository is a security-sensitive, multi-tenant B2B SaaS application. The following guidance is authoritative and must be followed for all Copilot suggestions and code generation inside this repo.

Core rules
----------
- Treat this as security-sensitive and multi-tenant: never suggest changes that weaken tenant isolation or leak data across `organization_id` boundaries.
- Architecture documentation in `docs/` is authoritative. Consult and reference [docs/architecture.md](docs/architecture.md) and [docs/mvp-scope.md](docs/mvp-scope.md) before proposing structural changes.
- Never introduce a new major dependency without explaining the rationale, trade-offs, and migration plan in the change description.
- Do not put business logic directly in UI components. Keep domain logic on the backend or in well-scoped shared libraries.
- Never make authorization decisions on the client. All authorization must be enforced server-side.
- Every tenant-owned database entity must include and be scoped by `organization_id`.
- Every schema change must be implemented via a migration. Do not suggest ad-hoc schema edits without migrations.
- Validate every API input and every AI-generated structure with explicit schemas and tests.
- Maintain a clear separation between quality assessment, risk assessment, authorization, and execution.
- Treat LLM output as untrusted input. Always validate, sanitize, and require provenance for any AI-generated content before consuming it.
- LLMs must never make final authorization decisions.
- Any external write or consequential action must pass deterministic authorization rules and be explicitly approved by the proper role.
- Preserve evidence and provenance for AI-generated findings: include pointers to evidence blobs, prompt versions, provider metadata, checksums, and timestamps.
- Consequential actions must have idempotency protection and explicit policy guards.
- Audit events are append-only. Do not alter or remove historical audit events.
- Never log secrets or raw sensitive artifact contents. Redact or hash sensitive inputs before including them in logs or traces.
- Use interfaces/abstractions for AI providers, storage providers, and external connectors; never bake provider-specific logic into domain models.
- Important domain behavior must be accompanied by automated tests. Do not propose behavior changes without corresponding tests.
- After making changes, run formatting, linting, type checking, and relevant tests. Do not suggest merging code that fails checks.
- Do not silently ignore failing tests: surface failures and recommend fixes or revert the change.
- Do not replace a working architecture merely to simplify a requested change. Prefer small, reviewable changes.
- When requirements are ambiguous, explain assumptions clearly in the change description and call them out in code comments or PR descriptions.

Developer and Copilot workflow expectations
------------------------------------------
- Prefer explicit domain code and small modules over framework magic.
- Favor migrations, typed schemas, and validated DTOs when modeling API and AI outputs.
- Record prompt templates and prompt versions as immutable artifacts; reference prompt versions in findings and audit events.
- Instrument LLM calls and background jobs for observability; redact sensitive content before exporting traces.
- For any suggested auto-remediation, ensure strict deterministic preconditions and include unit/integration tests demonstrating safety.

References
----------
- Architecture and MVP scope are authoritative: [docs/architecture.md](docs/architecture.md) and [docs/mvp-scope.md](docs/mvp-scope.md).

Administrative
--------------
- Do not modify application code yet unless explicitly instructed by a maintainer.
- If you propose changes that affect security, multitenancy, or data handling, include an ADR or link to an ADR proposal.
