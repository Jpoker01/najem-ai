"""Tests for constraints defined in db/schema.sql."""

import psycopg
import pytest

INSERT = """
    INSERT INTO fragment (id, law, valid, text)
    VALUES (%s, 'oz', %s::daterange, 'text')
"""


def test_overlapping_versions_of_one_fragment_are_rejected(db: psycopg.Connection) -> None:
    """Two versions of the same fragment must not be valid on the same day."""
    db.execute(INSERT, ("oz/par_2239/odst_1", "[2026-01-01,)"))
    with pytest.raises(psycopg.errors.ExclusionViolation):
        db.execute(INSERT, ("oz/par_2239/odst_1", "[2025-01-01,2027-01-01)"))


def test_consecutive_versions_of_one_fragment_are_allowed(db: psycopg.Connection) -> None:
    """A version ending on the day the next one starts does not overlap ([) bounds)."""
    db.execute(INSERT, ("oz/par_2239/odst_1", "[2021-07-01,2026-01-01)"))
    db.execute(INSERT, ("oz/par_2239/odst_1", "[2026-01-01,)"))
