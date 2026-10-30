"""Shared pytest fixtures."""

from collections.abc import Iterator

import psycopg
import pytest

from najem_ai.config import DATABASE_URL


@pytest.fixture
def db() -> Iterator[psycopg.Connection]:
    """Yield a connection inside a transaction that is rolled back after the test.

    The fragment table starts empty; the rollback restores any loaded data.
    """
    with psycopg.connect(DATABASE_URL) as conn:
        # why: rows from make load would collide with the ids the tests insert
        conn.execute("TRUNCATE fragment")
        yield conn
        conn.rollback()
