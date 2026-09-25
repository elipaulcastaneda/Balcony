from __future__ import annotations

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/balcony_dev"
)

# Ensure SQLAlchemy uses the installed driver (psycopg2) when the URL
# doesn't explicitly include a driver name. Some environments provide
# a plain `postgresql://` URL which defaults to psycopg (psycopg3).
if DATABASE_URL.startswith("postgresql://") and "+" not in DATABASE_URL.split("://", 1)[1]:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)

def get_session():
    return SessionLocal()
