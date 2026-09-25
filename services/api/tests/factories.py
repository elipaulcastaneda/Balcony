from __future__ import annotations

from sqlalchemy import insert
from app import models
import uuid


def create_organization(session, slug: str = None, name: str = None):
    slug = slug or f"org-{uuid.uuid4().hex[:8]}"
    name = name or slug
    org = models.Organization(slug=slug, name=name)
    session.add(org)
    session.commit()
    session.refresh(org)
    return org


def create_user(session, email: str = None, display_name: str = None):
    email = email or f"user-{uuid.uuid4().hex[:8]}@example.test"
    u = models.User(email=email, display_name=display_name or email)
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


def create_role(session, name: str):
    r = models.Role(name=name)
    session.add(r)
    session.commit()
    session.refresh(r)
    return r


def create_membership(session, org_id, user_id, role_id):
    m = models.OrganizationMembership(organization_id=org_id, user_id=user_id, role_id=role_id)
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


def create_artifact(session, org_id, created_by, name: str = "artifact"):
    a = models.Artifact(organization_id=org_id, created_by=created_by, name=name)
    session.add(a)
    session.commit()
    session.refresh(a)
    return a


def create_artifact_version(session, artifact_id, org_id, created_by, content_uri: str = "s3://bucket/key"):
    v = models.ArtifactVersion(artifact_id=artifact_id, organization_id=org_id, created_by=created_by, content_uri=content_uri, version=1)
    session.add(v)
    session.commit()
    session.refresh(v)
    return v


def create_audit_event(session, org_id, actor_id, event_type: str, entity_type: str = None, entity_id=None, request_id=None, metadata=None):
    e = models.AuditEvent(
        organization_id=org_id,
        actor_id=actor_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        request_id=request_id,
        metadata=metadata or {},
    )
    session.add(e)
    session.commit()
    session.refresh(e)
    return e
