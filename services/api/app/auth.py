from __future__ import annotations

from typing import Optional
from .models import OrganizationMembership, RolePermission
from .db import get_session
from sqlalchemy import select


def get_user_role_in_org(session, user_id, org_id) -> Optional[str]:
    q = select(OrganizationMembership).where(
        OrganizationMembership.user_id == user_id,
        OrganizationMembership.organization_id == org_id,
    )
    r = session.execute(q).scalars().first()
    return r.role_id if r else None


def authorize(user_id, org_id, permission: str) -> bool:
    """Simple authorize check: verifies user membership and role permission.

    Returns True when the user's role in the org contains the permission.
    """
    session = get_session()
    try:
        # find role id
        membership = (
            session.query(OrganizationMembership)
            .filter_by(user_id=user_id, organization_id=org_id)
            .first()
        )
        if not membership:
            return False
        # check permission
        rp = (
            session.query(RolePermission)
            .filter_by(role_id=membership.role_id, permission=permission)
            .first()
        )
        return rp is not None
    finally:
        session.close()
