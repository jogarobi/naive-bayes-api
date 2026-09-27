import os
from unittest.mock import patch

# Point the engine at an offline SQLite URL so importing the app never tries
# to reach the real Postgres database.
os.environ.setdefault("NEON_POSTGRES_DATABASE_URL", "sqlite://")

import pytest
from fastapi.testclient import TestClient

# Skip the create_all() DDL that main.py runs at import time; tests stub the
# service layer, so no schema is required.
with patch("app.models.Base.metadata.create_all"):
    from app.main import app


@pytest.fixture
def client():
    return TestClient(app)
