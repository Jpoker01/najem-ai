"""Spike: verify the e-Sbírka SPARQL endpoint returns versions and paragraph text."""

import requests

ENDPOINT = "https://opendata.eselpoint.gov.cz/sparql"
P = "https://slovník.gov.cz/datový/sbírka/pojem/"  # vocabulary prefix
ACT = "https://opendata.eselpoint.gov.cz/esel-esb/eli/cz/sb/2015/308"


def sparql(query: str) -> list[dict]:
    resp = requests.get(
        ENDPOINT,
        params={"query": query, "format": "application/sparql-results+json"},
        timeout=60,
    )
    resp.raise_for_status()
    # why: flatten {"var": {"type": ..., "value": ...}} to {"var": value}
    return [{k: v["value"] for k, v in row.items()} for row in resp.json()["results"]["bindings"]]


# 1) All versions of the act with their effective-from date
versions = sparql(f"""SELECT ?z ?d WHERE {{
  <{ACT}> <{P}má-znění> ?z .
  ?z <{P}účinnost-znění-od> ?d }}""")
for v in sorted(
    versions, key=lambda r: r["d"]
):  # why: sort in Python; ORDER BY returned 403 earlier
    print(v["d"], v["z"])

# 2) Text of § 5 in two versions (fragment -> content node -> text)
for version in ("2016-01-01", "2026-01-01"):
    rows = sparql(f"""SELECT ?f ?t WHERE {{
      ?f <{P}má-předka> <{ACT}/{version}/dokument/norma/par_5> .
      ?f <{P}obsahuje-fragment> ?c .
      ?c <{P}text-fragmentu> ?t }}""")
    print(f"\n=== § 5, version {version}")
    for r in rows:
        print("-", r["t"][:200])
