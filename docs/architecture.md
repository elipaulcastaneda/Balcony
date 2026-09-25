# Architecture: QC & Approval Platform (Procurement vertical slice)

Purpose
-------
This document captures the proposed system architecture, domain boundaries, security/trust considerations, major entities, lifecycle, API surface, repository layout, and ADR candidates for an MVP that provides a quality-control and approval layer for AI-assisted business artifacts. The first vertical slice targets "AI-assisted procurement analysis submitted for manager review."

High-level system architecture
------------------------------
- Frontend: Next.js + TypeScript (server-side rendering for secure pages, API client to backend). UI provides upload, review queue, findings display, and audit viewer.
- Backend API: FastAPI (Python) exposing an OpenAPI contract for the frontend and connectors. Implements server-side auth/authorization and tenant scoping.
- Database: PostgreSQL (single logical DB, tenant_id/organization_id column on tenant-owned records). Use migrations (Alembic).
- Object storage: S3-compatible (for uploaded documents, extracted artifact snapshots, and AI evidence blobs).
- Background worker(s): Async worker abstraction (e.g., Celery, Dramatiq, or RQ) for document processing, ML/LLM calls, quality checks, and remediation tasks.
- LLM provider abstraction: pluggable provider interface with adapters (OpenAI, Anthropic, local LLM gateways). All provider calls go through an adapter layer that records request/response provenance and prompt/version metadata.
- Connectors/adapters: Separate modules for external systems of record (ERP, CRM) used when writing back (post-approval). Initially stubbed and disabled.
- Observability: OpenTelemetry instrumentation for traces and metrics; redact sensitive artifact content in traces. Centralized logs with PII redaction policies.
- Immutable audit store: append-only audit log table (and optionally write-once blob store snapshots) to preserve events and evidence with cryptographic hashes.

Data flow (submission → approval)
----------------------------------
1. User/agent uploads artifact and supporting docs to frontend.
2. Frontend uploads content to S3 and creates an `Artifact` record via backend API.
3. Backend enqueues a processing job to worker.
4. Worker fetches artifact, extracts structured data (OCR, parsers), collects evidence (metadata, source docs), and runs quality checks and risk assessments via LLM adapters and deterministic rules.
5. Worker produces structured Findings and Risk objects; some issues flagged as remediable triggers automated remediation tasks (safe, deterministic fixes) that produce new artifact drafts.
6. If unresolved, backend routes to the appropriate reviewer queue and notifies manager.
7. Reviewer inspects findings, edits, approves/rejects; reviewer actions create AuditEvents.
8. Approved actions remain staged until an explicit write-back step (out-of-band and policy-controlled).

Domain boundaries
-----------------
- Artifact: submitted proposal/recommendation (procurement analysis in MVP).
- Evidence: uploaded documents, metadata, extracted text, LLM response contexts.
- Finding: a structured quality issue discovered by checks (with severity, category, provenance pointer).
- Remediation: an automated change or suggested change; must be deterministic for auto-remediation.
- Risk Assessment: structured risk score and rationale separate from quality findings.
- Review: human approval process, reviewer identity, decision (approve/reject/edit), comments.
- AuditEvent: immutable append-only record of system/user/AI actions and decisions.

Multi-tenant considerations
-------------------------
- Every tenant-owned table must include `organization_id` and tenant scoping enforced in every server-side query.
- Row-level security (RLS) is recommended as an additional layer but not the only mechanism; API must always verify tenant scope.

Major database entities and relationships
---------------------------------------
- `Organization` (id, name, admin(s) pointers, config)
- `User` (id, organization_id, email, role, hashed_auth_id)
- `Artifact` (id, organization_id, submitted_by, kind, status, s3_path, created_at)
- `Evidence` (id, artifact_id, organization_id, s3_path, extracted_text_ref)
- `Finding` (id, artifact_id, organization_id, severity, type, structured_payload, provenance_refs, created_by=system/LLM/rule)
- `RiskAssessment` (id, artifact_id, organization_id, score, vector, rationale_blob)
- `Remediation` (id, artifact_id, organization_id, type, status, applied_by, diff_blob)
- `Review` (id, artifact_id, reviewer_id, decision, comments, started_at, completed_at)
- `AuditEvent` (id, organization_id, event_type, actor_id, payload_ref, created_at, immutable_hash)
- `PromptVersion` (id, name, version, template, checksum, author_id, created_at)

Relationships (summary)
- `Organization` 1–* `User`
- `Artifact` 1–* `Evidence`
- `Artifact` 1–* `Finding`
- `Artifact` 1–1 `RiskAssessment` (initial), with historical snapshots allowed
- `Artifact` 1–* `Review`
- `Artifact` 1–* `AuditEvent`

Artifact lifecycle / state machine
----------------------------------
States (MVP): Submitted -> Processing -> Ready | Remediable | Routed -> UnderReview -> Approved | Rejected -> Closed

Transitions (high level):
- `Submitted` (created by user) -> `Processing` (job enqueued)
- `Processing` -> `Ready` (no findings of concern)
- `Processing` -> `Remediable` (only remediable issues found; worker applies safe remediations or flags remediation suggestions)
- `Processing` -> `Routed` (non-remediable issues found)
- `Remediable` -> `Ready` (after automatic remediation succeeded) or -> `Routed` (if auto-remediation fails or needs human confirmation)
- `Routed` -> `UnderReview` (manager begins review)
- `UnderReview` -> `Approved` (manager approves) or -> `Rejected` (manager rejects or requests changes)
- `Approved` -> `Closed` (optional finalization after write-back step)

Notes:
- Every state transition must generate an `AuditEvent` with pointers to the evidence and prompt versions that produced findings.
- State machine implementation should be explicit in domain logic (no implicit DB-only flags).

API boundaries (OpenAPI contract highlights)
-----------------------------------------
Authentication/Authorization
- `POST /auth/login` (token issued by identity provider)
- `GET /auth/me`

Artifact lifecycle
- `POST /v1/organizations/{org_id}/artifacts` — create artifact (uploads return S3 URL or presigned URL)
- `GET /v1/organizations/{org_id}/artifacts/{artifact_id}` — fetch artifact metadata and status
- `GET /v1/organizations/{org_id}/artifacts?status=...` — list (paginated) for review queues
- `POST /v1/organizations/{org_id}/artifacts/{id}/evidence` — attach evidence

Processing & findings
- `GET /v1/organizations/{org_id}/artifacts/{id}/findings`
- `GET /v1/organizations/{org_id}/artifacts/{id}/risk`
- `POST /v1/organizations/{org_id}/artifacts/{id}/remediation/apply` — request deterministic remediation (server-side checks required)

Review actions
- `POST /v1/organizations/{org_id}/artifacts/{id}/reviews` — reviewer decision (approve/reject/edit)
- `GET /v1/organizations/{org_id}/reviews/queue` — fetch assigned items

Audit & prompts
- `GET /v1/organizations/{org_id}/artifacts/{id}/audit` — immutable event stream
- `GET /v1/organizations/{org_id}/prompt-versions` — list prompt templates and versions

Operational/Administration
- `POST /v1/admin/tenants` — tenant provisioning (admin only)

Authorization model
-------------------
- Centralized server-side checks for every API: validate `organization_id` in path, validate user's membership and role.
- Never rely on AI to authorize. Human approvals must come from an explicitly authorized reviewer record.
- Least privilege: expose reviewer assignment endpoints so permissions are narrowly scoped.

Provenance and reproducibility
-------------------------------
- All LLM calls must record: provider, model, model_version, prompt_version_id, inputs (hashed or redacted), response pointer (S3) and checksum, and execution timestamp.
- Findings must reference the exact evidence items and LLM prompt versions used to create them.
- Prompt templates are versioned (`PromptVersion`) and immutable once used in production evaluations.

Security and privacy
--------------------
- Secrets: use vault (e.g., AWS Secrets Manager or HashiCorp Vault) for provider keys; do not store in repo or plain config.
- Logging: redact sensitive payloads; store extracted_text and evidence in protected S3 with least-privilege access.
- Data residency: allow tenant configuration for storage region if required.
- Rate limiting and provider quotas applied at adapter level.

Observability
-------------
- Instrument FastAPI, workers, and LLM adapters with OpenTelemetry.
- Capture traces for processing jobs; redact PII at the boundary before exporting.

Repository layout (recommended)
------------------------------
- /apps/frontend — Next.js TypeScript app
- /apps/backend — FastAPI app
- /services/worker — worker tasks and adapters
- /libs/llm-adapters — provider interfaces and implementations
- /libs/common — shared types, OpenAPI client, DB models
- /migrations — Alembic migrations
- /infra — Docker compose, dev scripts, localstack-compose (S3), and observability configs
- /tests/backend — pytest tests
- /tests/e2e — Playwright tests for UI flows
- /docs — design and operational docs (this file lives here)

ADR candidates
--------------
1. Multitenancy strategy: single DB with `organization_id` vs one-db-per-tenant.
2. Worker choice: Celery vs Dramatiq vs RQ.
3. LLM provider abstraction contract and schema for evidence provenance.
4. Audit model: relational append-only vs WORM storage with cryptographic anchoring.
5. Automatic remediation policy: which classes of fixes are permitted for auto-run.

What would be overengineering for the MVP
----------------------------------------
- Microservice split by domain (keep monolith-with-well-defined-modules first).
- Full connector implementations to ERP/financial systems (stub them; require explicit enablement post-MVP).
- Complex RBAC engines; begin with role-based scopes (user, reviewer, admin) and server-side checks.
- Distributed tracing across many services before load justifies it; instrument, but keep simple collectors.

Next steps (recommended immediate work items)
-------------------------------------------
1. Create `docs/mvp-scope.md` (vertical slice definition).
2. Scaffold repository layout and minimal FastAPI + Next.js templates.
3. Implement DB schema migrations for core tables (`Organization`, `User`, `Artifact`, `Finding`, `AuditEvent`).
4. Implement LLM adapter interface and prompt-versioning model.
