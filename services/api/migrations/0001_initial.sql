-- Initial schema: organizations, users, roles, membership, artifacts, versions, audit
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Organizations
CREATE TABLE IF NOT EXISTS organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Users (global)
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  display_name TEXT,
  hashed_password TEXT,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Roles and permissions
CREATE TABLE IF NOT EXISTS roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT UNIQUE NOT NULL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS role_permissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  permission TEXT NOT NULL,
  UNIQUE(role_id, permission)
);

-- Organization membership
CREATE TABLE IF NOT EXISTS organization_membership (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role_id UUID NOT NULL REFERENCES roles(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(organization_id, user_id)
);

-- Artifacts
CREATE TABLE IF NOT EXISTS artifacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  created_by UUID NOT NULL REFERENCES users(id),
  name TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Artifact versions (immutable)
CREATE TABLE IF NOT EXISTS artifact_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  artifact_id UUID NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  created_by UUID NOT NULL REFERENCES users(id),
  content_uri TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  immutable_metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(artifact_id, version)
);

-- Audit events (append-only)
CREATE TABLE IF NOT EXISTS audit_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  actor_id UUID NULL REFERENCES users(id),
  event_type TEXT NOT NULL,
  entity_type TEXT,
  entity_id UUID NULL,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  request_id UUID NULL,
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Row Level Security: tenant isolation using app.current_organization
-- Enable RLS on tenant-owned tables
ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE artifact_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;

-- Policy allowing only rows matching the current organization
CREATE POLICY tenant_isolation_artifacts ON artifacts
  USING (organization_id::text = current_setting('app.current_organization', true))
  WITH CHECK (organization_id::text = current_setting('app.current_organization', true));

CREATE POLICY tenant_isolation_artifact_versions ON artifact_versions
  USING (organization_id::text = current_setting('app.current_organization', true))
  WITH CHECK (organization_id::text = current_setting('app.current_organization', true));

CREATE POLICY tenant_isolation_audit_events ON audit_events
  USING (organization_id::text = current_setting('app.current_organization', true))
  WITH CHECK (organization_id::text = current_setting('app.current_organization', true));

-- Prevent updates/deletes on artifact_versions (immutability)
CREATE OR REPLACE FUNCTION prevent_artifact_versions_modifications()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'artifact_versions are immutable';
END;
$$;
CREATE TRIGGER trg_prevent_artifact_versions_mods
  BEFORE UPDATE OR DELETE ON artifact_versions
  FOR EACH ROW EXECUTE FUNCTION prevent_artifact_versions_modifications();

-- Prevent updates/deletes on audit_events (append-only)
CREATE OR REPLACE FUNCTION prevent_audit_events_modifications()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'audit_events are append-only';
END;
$$;
CREATE TRIGGER trg_prevent_audit_events_mods
  BEFORE UPDATE OR DELETE ON audit_events
  FOR EACH ROW EXECUTE FUNCTION prevent_audit_events_modifications();
