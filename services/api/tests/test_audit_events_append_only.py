from tests.factories import create_organization, create_user, create_role, create_membership, create_audit_event
from tests.conftest import set_current_org
import pytest


def test_audit_events_append_only(db_session):
    org = create_organization(db_session, slug="org-audit", name="Org Audit")
    user = create_user(db_session, email="carol@example.test")
    role = create_role(db_session, name="admin")
    create_membership(db_session, org.id, user.id, role.id)

    set_current_org(db_session, org.id)
    e = create_audit_event(db_session, org.id, user.id, event_type="artifact.created", entity_type="artifact", entity_id=None, metadata={"note": "ok"})

    # Attempt to update should raise
    with pytest.raises(Exception):
        db_session.execute("UPDATE audit_events SET metadata = '{}' WHERE id = :id", {"id": e.id})
        db_session.commit()
