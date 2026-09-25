from tests.factories import create_organization, create_user, create_role, create_membership, create_artifact
from tests.conftest import set_current_org


def test_organization_isolation(db_session):
    # create two organizations and users
    org_a = create_organization(db_session, slug="org-a", name="Org A")
    org_b = create_organization(db_session, slug="org-b", name="Org B")

    user = create_user(db_session, email="alice@example.test")
    role = create_role(db_session, name="member")
    # give user membership only in org_a
    create_membership(db_session, org_a.id, user.id, role.id)

    # create an artifact in org_b
    artifact_b = create_artifact(db_session, org_b.id, user.id, name="secret-artifact")

    # act as org_a: set current org and assert artifact in org_b is not visible
    set_current_org(db_session, org_a.id)
    rows = db_session.execute("SELECT id FROM artifacts WHERE id = :id", {"id": artifact_b.id}).fetchall()
    assert len(rows) == 0

    # act as org_b: should be visible
    set_current_org(db_session, org_b.id)
    rows = db_session.execute("SELECT id FROM artifacts WHERE id = :id", {"id": artifact_b.id}).fetchall()
    assert len(rows) == 1
