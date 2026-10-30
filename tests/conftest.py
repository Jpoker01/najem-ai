"""Shared pytest fixtures."""

import os
from collections.abc import Iterator

import psycopg
import pytest

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://najemai:najemai@localhost:5432/najemai",
)


@pytest.fixture
def db() -> Iterator[psycopg.Connection]:
    """Yield a connection inside a transaction that is rolled back after the test."""
    with psycopg.connect(DATABASE_URL) as conn:
        yield conn
        conn.rollback()
