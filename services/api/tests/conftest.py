import os
import subprocess
import time
import pytest
import sys
import uuid
from pathlib import Path
from sqlalchemy import text

# Ensure the service package path is on sys.path so imports work when pytest
# is invoked from the repository root.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _start_test_postgres_container():
    name = f"balcony_test_{uuid.uuid4().hex[:8]}"
    # Start an ephemeral Postgres container publishing to a random host port
    subprocess.run([
        "docker",
        "run",
        "-d",
        "-e",
        "POSTGRES_PASSWORD=postgres",
        "-e",
        "POSTGRES_DB=balcony_test",
        "-P",
        "--name",
        name,
        "postgres:15",
    ], check=True)

    out = subprocess.check_output(["docker", "port", name, "5432"]).decode().strip()
    host_port = out.split(":")[-1]
    return name, host_port


@pytest.fixture(scope="session")
def ensure_db_running():
    """Start a temporary Postgres container for the test session when possible.

    Sets `DATABASE_URL` to point to the container so the DB helpers and init
    script use the correct DB. If Docker is not available, falls back to
    docker-compose up -d db if possible. If neither can run, tests using the
    DB will be skipped.
    """
    container_name = None
    try:
        # Try docker run path
        container_name, host_port = _start_test_postgres_container()
        os.environ["DATABASE_URL"] = f"postgresql://postgres:postgres@localhost:{host_port}/balcony_test"

        # Wait for Postgres to accept connections
        for _ in range(30):
            try:
                # Use pg_isready inside the container for a reliable check
                rc = subprocess.run(["docker", "exec", container_name, "pg_isready", "-U", "postgres"], check=False)
                if rc.returncode == 0:
                    break
            except Exception:
                pass
            time.sleep(1)
        else:
            raise RuntimeError("Timed out waiting for test Postgres to become available")

        yield
    except Exception:
        # Fallback to docker-compose up -d db (best-effort)
        try:
            compose_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "infra", "docker-compose.yml"))
            subprocess.run(["docker", "compose", "-f", compose_file, "up", "-d", "db"], check=True, env=os.environ.copy())
            # Wait briefly
            time.sleep(2)
            # Ensure DATABASE_URL points to localhost default
            os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/balcony_dev")
            yield
        except Exception:
            # Could not start a DB; yield so db_session can skip if needed
            yield
    finally:
        if container_name:
            try:
                subprocess.run(["docker", "rm", "-f", container_name], check=False)
            except Exception:
                pass


@pytest.fixture(scope="session")
def db_engine(ensure_db_running):
    # Import engine after DATABASE_URL has been set by ensure_db_running
    from app.db import engine

    return engine


@pytest.fixture()
def db_session(db_engine):
    # ensure schema exists by running the init script
    init_script = Path(__file__).parent.parent.joinpath("scripts", "init_db.py").resolve()
    try:
        subprocess.run([sys.executable, str(init_script)], check=True, env=os.environ.copy())
    except subprocess.CalledProcessError as e:
        pytest.skip(f"Database initialization failed: {e}")

    from app.db import get_session

    sess = get_session()
    try:
        yield sess
    finally:
        sess.close()


def set_current_org(session, org_id):
    # set per-transaction setting so RLS policies can read it
    session.execute(text("SELECT set_config('app.current_organization', :val, true);"), {"val": str(org_id)})
    session.commit()
