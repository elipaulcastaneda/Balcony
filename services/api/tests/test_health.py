from app.main import healthz


def test_health():
    # Directly call the health function to avoid heavy test client deps in CI bootstrap
    assert healthz() == {"status": "ok"}
