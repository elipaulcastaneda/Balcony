def healthz():
    return {"status": "ok"}


# Create FastAPI app only if FastAPI is installed; keep module import-light for tests/setup
try:
    from fastapi import FastAPI

    app = FastAPI(title="Balcony QC API")

    @app.get("/healthz")
    def _healthz():
        return healthz()
except Exception:
    app = None
