from tests.factories import create_organization, create_user, create_role, create_membership, create_artifact_version, create_artifact
from tests.conftest import set_current_org
import pytest


def test_artifact_version_immutable(db_session):
    org = create_organization(db_session, slug="org-immut", name="Org Immut")
    user = create_user(db_session, email="bob@example.test")
    role = create_role(db_session, name="member")
    create_membership(db_session, org.id, user.id, role.id)

    art = create_artifact(db_session, org.id, user.id, name="immut-art")
    v = create_artifact_version(db_session, art.id, org.id, user.id)

    set_current_org(db_session, org.id)

    # Attempt to update should raise an exception raised by trigger
    with pytest.raises(Exception):
        db_session.execute("UPDATE artifact_versions SET content_uri = 'x' WHERE id = :id", {"id": v.id})
        db_session.commit()
