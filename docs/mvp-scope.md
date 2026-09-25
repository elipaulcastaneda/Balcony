# MVP Scope: Procurement Vertical Slice

Goal
----
Deliver an initial vertical slice that demonstrates the core value: a human-in-the-loop quality-control and approval flow for AI-assisted procurement recommendations, with full provenance and immutable audit history.

Primary success criteria (MVP acceptance)
----------------------------------------
- An employee can submit a procurement recommendation and supporting documents.
- The system extracts the artifact, runs deterministic business-rule checks and LLM-assisted quality checks, and produces structured `Finding` objects with provenance.
- The system computes a `RiskAssessment` for the artifact.
- Safe, deterministic remediations are applied automatically when allowed; otherwise the artifact is routed to the manager's review queue.
- A manager can review, edit (minor edits or attach comments), and approve or reject the artifact.
- All actions produce immutable `AuditEvent`s that include references to the evidence and prompt versions used.
- No automatic, consequential external actions (no write-back to ERP in MVP).

Scope: in-scope (MVP)
---------------------
- Single artifact type: `procurement_analysis` (structured fields: title, requested_amount, vendor_recommendation, justification_text, supporting_documents).
- Upload UI and presigned S3 uploads for supporting documents.
- Extraction pipeline: text extraction (OCR optional), metadata capture, and simple structured extraction rules.
- Deterministic business-rule checks (e.g., vendor allowed, threshold checks, required fields present).
- LLM-assisted quality checks to identify clarity, missing evidence, conflicting claims — LLM output must be validated and rendered as structured `Finding`s with provenance.
- Risk scoring (simple rule-based + optional LLM rationale capture) with structured score and rationale.
- Auto-remediation limited to safe fixes (e.g., normalize currency formatting, populate missing standardized vendor code when unambiguous).
- Reviewer flow with approve/reject/edit and audit trail.
- Basic multi-tenant enforcement: `organization_id` on records and server-side scoping.
- Tests: pytest unit tests for backend domain logic; Playwright e2e for submission → review happy path.

Out of scope (post-MVP)
-----------------------
- Multiple artifact kinds beyond procurement_analysis.
- Full ERP/financial system write-backs.
- Sophisticated role/permission DSL or enterprise SSO integrations beyond a simple OIDC/OAuth path.
- Advanced automated remediations that can change financial commitments.
- Multi-region data residency controls.

Operational constraints and minimal infra for MVP
-------------------------------------------------
- Local development via Docker Compose (Postgres, MinIO for S3, localstack optional).
- LLM provider keys held in a dev vault or passed at runtime via env; provider adapter must allow mocking.
- Background worker (single process) for job processing in dev.

API contract highlights for MVP
-----------------------------
- `POST /v1/organizations/{org_id}/artifacts` — create procurement artifact (returns artifact id and upload instructions)
- `POST /v1/organizations/{org_id}/artifacts/{id}/evidence` — upload evidence metadata (S3 path)
- `GET /v1/organizations/{org_id}/artifacts/{id}/status` — processing status and findings pointer
- `GET /v1/organizations/{org_id}/artifacts/{id}/findings` — structured findings with provenance
- `POST /v1/organizations/{org_id}/artifacts/{id}/reviews` — reviewer decision
- `GET /v1/organizations/{org_id}/reviews/queue` — manager review queue

Testing and verification
------------------------
- Unit tests (pytest) covering: rule engine, state transitions, provenance recording, prompt-versioning behavior.
- Integration test(s) for worker pipeline using small test artifacts.
- E2E Playwright tests for submission → auto-processing → routing → review → approval.

Security/trust controls (MVP minimal)
------------------------------------
- Server-side tenant scoping on every API.
- Prompt-versioning and immutable evidence references for traceability.
- No plain-text secret commits; environment-based secret injection.
- Audit events must be write-once in the DB (append-only) and reference S3 evidence, not inline PII.

Developer deliverables (MVP implementation checklist)
----------------------------------------------------
- Scaffolds: Next.js app (upload + review pages) and FastAPI backend (OpenAPI schema generated).
- DB migrations for core tables.
- Worker job for processing procurement artifacts to produce Findings and RiskAssessment.
- LLM adapter interface and a mock adapter for tests.
- Prompt versioning workflow (create/list prompt versions).
- Basic observability instrumentation (request-level traces, job traces).
- Tests: pytest and Playwright happy-path.

Acceptance criteria (concrete)
-----------------------------
1. Given a procurement artifact uploaded by a user, the system processes it and returns a `findings` list and `risk` object within a reasonable time (configurable worker SLA).
2. Given findings requiring human review, the artifact appears in the manager's queue and the manager can approve/reject with an audit entry recorded.
3. All findings include `provenance_refs` that link to evidence blobs and `prompt_version` used.
4. No external system changes occur automatically as a result of approval (write-back disabled by default).

Minimum UI wireframes (textual)
-------------------------------
- Submit page: form fields for procurement_analysis + upload supporting documents.
- Artifact status: shows current state, findings list with severity badges, risk score, and audit timeline.
- Review queue: list of artifacts assigned to a manager with quick-approve actions and view-details.

Notes & constraints
-------------------
- Keep LLM usage auditable and replaceable; do not bake provider-specific logic into domain models.
- Keep auto-remediation conservative and explicit: require exact deterministic preconditions.
- Keep the initial domain model small and iteratively expand.
