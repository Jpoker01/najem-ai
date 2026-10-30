"""Load the parsed fragments into the fragment table in Postgres.

The table is emptied and refilled in one transaction, so a failed load keeps the old data.
Run from the repo root: uv run python -m najem_ai.ingest.load
"""

from collections import Counter

import psycopg
from psycopg.types.range import Range

from najem_ai.config import DATABASE_URL
from najem_ai.ingest.parse import Row, parse_all

INSERT = """
    INSERT INTO fragment (id, law, par, odst, pism, citation, valid, text)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""


def load(rows: list[Row], conn: psycopg.Connection) -> None:
    """Replace everything in the fragment table with rows, in one transaction.

    lemmas and embedding stay NULL; later steps fill them in.
    """
    params = []
    for row in rows:
        f = row.fragment
        # valid_to=None gives an open upper bound: still in force
        valid = Range(row.valid_from, row.valid_to, "[)")
        params.append((f.id, f.law, f.par, f.odst, f.pism, f.citation, valid, f.text))

    with conn.transaction(), conn.cursor() as cur:
        cur.execute("TRUNCATE fragment")
        cur.executemany(INSERT, params)


def main() -> None:
    """Load every parsed fragment and print how many rows each law got."""
    rows = parse_all()
    with psycopg.connect(DATABASE_URL) as conn:
        load(rows, conn)
    counts = Counter(row.fragment.law for row in rows)
    for law, count in sorted(counts.items()):
        print(f"{law}: {count} rows")


if __name__ == "__main__":
    main()
