"""Download the in-scope tenancy law from e-Sbírka (SPARQL) into data/raw/.

Follows act -> version -> fragments (§, odstavce, písmena) -> text for every version from 1 Jul 2021,
and records each file's query and SHA-256 in data/raw/manifest.json.
Run from the repo root.
"""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import requests

ENDPOINT = "https://opendata.eselpoint.gov.cz/sparql"
ELI = "https://opendata.eselpoint.gov.cz/esel-esb/eli/cz/sb/"
P = "https://slovník.gov.cz/datový/sbírka/pojem/"  # e-Sbírka vocabulary
XSD_STRING = "http://www.w3.org/2001/XMLSchema#string"
RAW = Path("data/raw")
MAX_DEPTH = 8  # 3-4 is necessary, 8 just to be safe

# versions = the wording in force on 1 Jul 2021 plus every later version in
# which the in-scope text changed (found on 27 Oct 2026 by diffing all versions)
SOURCES = {
    "oz": {
        "eli": "2012/89",
        "versions": ["2021-07-01", "2026-01-01"],
        "roots": [
            "dokument/norma/cast_4/hlava_2/dil_2/oddil_3/pododdil_1",  # § 2201-2234
            "dokument/norma/cast_4/hlava_2/dil_2/oddil_3/pododdil_2",  # § 2235-2301
        ],
    },
    "nv308": {
        "eli": "2015/308",
        "versions": ["2016-01-01", "2026-01-01"],
        "roots": ["dokument/norma"],
    },
    "z67": {
        "eli": "2013/67",
        "versions": ["2020-07-01", "2023-01-01", "2024-01-01", "2026-01-01", "2027-01-01"],
        "roots": ["dokument/norma"],
    },
    "osr": {
        "eli": "1963/99",
        "versions": ["2021-07-01", "2024-07-01", "2025-01-01", "2026-01-01"],
        "citations": ["§ 114b", "§ 172", "§ 173", "§ 174", "§ 175a", "§ 195", "§ 196"],
    },
}


def sparql(query: str) -> bytes:
    """Run a SPARQL query against ENDPOINT and return the raw JSON response bytes."""
    resp = requests.get(
        ENDPOINT,
        params={"query": query, "format": "application/sparql-results+json"},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.content


def bindings(raw: bytes) -> list[dict]:
    """Turn a SPARQL JSON response into a list of {variable: value} rows."""
    response = json.loads(raw)
    result_rows = response["results"]["bindings"]

    rows = []
    for result_row in result_rows:
        # each cell looks like {"type": "literal", "value": "..."}; keep only the value
        row = {}
        for variable, cell in result_row.items():
            row[variable] = cell["value"]
        rows.append(row)
    return rows


def save(path: Path, query: str, manifest: dict) -> list[dict]:
    """Run the query, write the response to path, record it in manifest and return its rows."""
    raw = sparql(query)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    manifest[path.relative_to(RAW).as_posix()] = {
        "endpoint": ENDPOINT,
        "query": query,
        "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    return bindings(raw)


def versions_query(act_iri: str) -> str:
    """Build a query listing every version of an act with its effective date and type."""
    return f"""SELECT ?version ?valid_from ?kind WHERE {{
  <{act_iri}> <{P}má-znění> ?version .
  OPTIONAL {{ ?version <{P}účinnost-znění-od> ?valid_from }}
  OPTIONAL {{ ?version <{P}má-typ-znění-právního-aktu> ?kind }} }}"""


def citations_query(version_iri: str, citations: list[str]) -> str:
    """Build a query finding the fragments of a version whose citation label (e.g. "§ 172") is listed."""
    values = " ".join(f'"{c}"^^<{XSD_STRING}>' for c in citations)
    return f"""SELECT ?cit ?f WHERE {{
  VALUES ?cit {{ {values} }}
  <{version_iri}> <{P}má-fragment-znění> ?f .
  ?f <{P}citace-označení-fragmentu-znění-právního-aktu> ?cit }}"""


def descendants_query(root_iri: str, depth: int) -> str:
    """Build a query for the fragments exactly depth levels below root_iri, with their order, citation, type and text."""
    chain = [f"?x0 <{P}má-předka> <{root_iri}> ."]
    chain += [f"?x{i} <{P}má-předka> ?x{i - 1} ." for i in range(1, depth)]
    return f"""SELECT ?f ?order ?cit ?c ?type ?text WHERE {{
  {" ".join(chain)}
  BIND(?x{depth - 1} AS ?f)
  ?f <{P}obsahuje-fragment> ?c .
  OPTIONAL {{ ?f <{P}pořadí-fragmentu-znění-právního-aktu> ?order }}
  OPTIONAL {{ ?f <{P}citace-označení-fragmentu-znění-právního-aktu> ?cit }}
  OPTIONAL {{ ?c <{P}má-typ-fragmentu> ?type }}
  OPTIONAL {{ ?c <{P}text-fragmentu> ?text }} }}"""


def fetch_root(name: str, version: str, label: str, root_iri: str, manifest: dict) -> int:
    """Save every level below root_iri (one file per depth, up to MAX_DEPTH) and return the total row count."""
    total = 0
    for depth in range(1, MAX_DEPTH + 1):
        rows = save(
            RAW / name / version / f"{label}.d{depth}.json",
            descendants_query(root_iri, depth),
            manifest,
        )
        if not rows:
            break  # why: no fragments at this depth means none deeper either
        total += len(rows)
    return total


def main() -> None:
    """Fetch every act, version and root in SOURCES into data/raw/ and write manifest.json."""
    manifest: dict = {}
    for name, src in SOURCES.items():
        act_iri = ELI + src["eli"]
        save(RAW / name / "versions.json", versions_query(act_iri), manifest)
        for version in src["versions"]:
            version_iri = f"{act_iri}/{version}"
            if "roots" in src:
                roots = {r.rsplit("/", 1)[1]: f"{version_iri}/{r}" for r in src["roots"]}
            else:
                rows = save(
                    RAW / name / version / "citations.json",
                    citations_query(version_iri, src["citations"]),
                    manifest,
                )
                roots = {r["f"].rsplit("/", 1)[1]: r["f"] for r in rows}
                missing = set(src["citations"]) - {r["cit"] for r in rows}
                if missing:
                    print(f"{name} {version}: not in this version: {sorted(missing)}")
            for label, root_iri in roots.items():
                n = fetch_root(name, version, label, root_iri, manifest)
                print(f"{name} {version} {label}: {n} fragments")
        # why: written after every act so a crash keeps what was already fetched
        (RAW / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8"
        )


if __name__ == "__main__":
    main()
