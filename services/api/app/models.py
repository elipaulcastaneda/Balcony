from __future__ import annotations

import enum
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
import uuid

Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    slug = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    email = Column(String, nullable=False, unique=True)
    display_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class Role(Base):
    __tablename__ = "roles"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)


class RolePermission(Base):
    __tablename__ = "role_permissions"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission = Column(String, nullable=False)


class OrganizationMembership(Base):
    __tablename__ = "organization_membership"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("organization_id", "user_id", name="uix_org_user"),)


class Artifact(Base):
    __tablename__ = "artifacts"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class ArtifactVersion(Base):
    __tablename__ = "artifact_versions"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    artifact_id = Column(UUID(as_uuid=True), ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content_uri = Column(String, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    immutable_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("artifact_id", "version", name="uix_artifact_version"),)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_type = Column(String, nullable=False)
    entity_type = Column(String)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    request_id = Column(UUID(as_uuid=True), nullable=True)
    metadata = Column(JSON, nullable=False, default=dict)
