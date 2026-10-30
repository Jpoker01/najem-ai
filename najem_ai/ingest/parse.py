"""Parse the raw SPARQL responses in data/raw/ into citable fragments with validity ranges.

Each kept odstavec, písmeno or bod becomes one fragment with a version-independent id
(e.g. oz/par_2239/odst_1). Headings and the bare "§ X" labels are skipped, the HTML is
cleaned out of the text, and only § marked keep in data/scope.json are included.
A version is valid until the next fetched version starts; consecutive versions with the
same text are merged into one row.
Run from the repo root.
"""

import html
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from najem_ai.config import LEVELS, RAW, SCOPE, SEGMENT, TEXT_TYPES

# the only superscripts in the data: m² and footnote marks like ¹)
SUPERSCRIPTS = {"<sup>1</sup>": "¹", "<sup>2</sup>": "²"}


@dataclass(frozen=True)
class Fragment:
    """One citable piece of text in one version of a law."""

    id: str  # version-independent path, e.g. oz/par_2239/odst_1
    law: str
    par: str | None
    odst: str | None
    pism: str | None
    citation: str | None  # "§ 2239 odst. 1" as stored by e-Sbírka; None for an unnumbered odstavec
    text: str


@dataclass(frozen=True)
class Row:
    """A fragment with the range of days its text is in force: [valid_from, valid_to)."""

    fragment: Fragment
    valid_from: date
    valid_to: date | None  # None = still in force


def clean_text(raw: str) -> str:
    """Strip HTML tags, unescape entities and collapse whitespace."""
    text = raw
    # replace m<sup>2</sup> with m² and footnote marks <sup>1</sup>) with ¹)
    for tag, char in SUPERSCRIPTS.items():
        text = text.replace(tag, char)
    # remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # turn escaped characters back into their original form
    text = html.unescape(text)
    # replace each run of whitespace with a single space
    return re.sub(r"\s+", " ", text).strip()


def load_scope(path: Path = SCOPE) -> set[str]:
    """Return the § keys marked keep in scope.json, e.g. {"oz/par_2239", ...}."""
    paragraphs = json.loads(path.read_text(encoding="utf-8"))["paragraphs"]
    return {key for key, entry in paragraphs.items() if entry["label"] == "keep"}


def parse_binding(law: str, binding: dict) -> Fragment | None:
    """Turn one SPARQL result row into a Fragment, or None if it is not citable text."""
    row = {variable: cell["value"] for variable, cell in binding.items()}
    if row.get("type", "").rsplit("/", 1)[-1] not in TEXT_TYPES:
        return None
    text = clean_text(row.get("text", ""))
    if not text:
        return None

    parts = {}
    for segment in row["f"].split("/"):
        match = SEGMENT.fullmatch(segment)
        if match:
            parts[match[1]] = match[2]
    if "par" not in parts:
        return None

    id_parts = [law]
    for level in LEVELS:
        if level in parts:
            id_parts.append(f"{level}_{parts[level]}")
    fragment_id = "/".join(id_parts)  # e.g. osr/par_175a/odst_2/pism_a

    return Fragment(
        id=fragment_id,
        law=law,
        par=parts["par"],
        odst=parts.get("odst"),
        pism=parts.get("pism"),
        citation=row.get("cit"),
        text=text,
    )


def parse_version(law: str, version_dir: Path, scope: set[str]) -> dict[str, Fragment]:
    """Return the in-scope fragments of one version of a law, keyed by id."""
    fragments = {}
    for path in sorted(version_dir.glob("*.d*.json")):
        bindings = json.loads(path.read_text(encoding="utf-8"))["results"]["bindings"]
        for binding in bindings:
            fragment = parse_binding(law, binding)
            if fragment is None or f"{law}/par_{fragment.par}" not in scope:
                continue
            if fragment.id in fragments and fragments[fragment.id] != fragment:
                raise ValueError(f"{version_dir}: two different fragments with id {fragment.id}")
            fragments[fragment.id] = fragment
    return fragments


def build_ranges(versions: list[tuple[date, dict[str, Fragment]]]) -> list[Row]:
    """Give each fragment a validity range from a list of (start date, fragments) versions.
    A version is valid until the next one starts (the last one stays open). If a fragment
    has the same content in consecutive versions, they are merged into one row; if it is
    missing from a version, its row ends where that version starts.
    """
    versions = sorted(versions, key=lambda v: v[0])
    ends = [start for start, _ in versions[1:]] + [
        None
    ]  # each version ends where the next starts
    ids = sorted({i for _, fragments in versions for i in fragments})
    rows = []
    for fragment_id in ids:
        for (start, fragments), end in zip(versions, ends):
            fragment = fragments.get(fragment_id)
            if fragment is None:
                continue
            last = rows[-1] if rows else None
            # same text continuing straight on: extend the previous row instead of adding one
            if last and last.fragment == fragment and last.valid_to == start:
                rows[-1] = Row(fragment, last.valid_from, end)
            else:
                rows.append(Row(fragment, start, end))
    return rows


def parse_law(law: str, scope: set[str], raw: Path = RAW) -> list[Row]:
    """Parse every fetched version of one law (one data/raw/<law>/<date>/ folder each)."""
    versions = [
        (date.fromisoformat(version_dir.name), parse_version(law, version_dir, scope))
        for version_dir in (raw / law).iterdir()
        if version_dir.is_dir()
    ]
    return build_ranges(versions)


def parse_all(raw: Path = RAW, scope_path: Path = SCOPE) -> list[Row]:
    """Parse every law in data/raw/ into rows for the fragment table."""
    scope = load_scope(scope_path)
    rows = []
    for law_dir in sorted(raw.iterdir()):
        if law_dir.is_dir():
            rows += parse_law(law_dir.name, scope, raw)
    return rows


def main() -> None:
    """Print how many rows each law produced."""
    rows = parse_all()
    for law in sorted({row.fragment.law for row in rows}):
        law_rows = [row for row in rows if row.fragment.law == law]
        ids = {row.fragment.id for row in law_rows}
        print(f"{law}: {len(law_rows)} rows, {len(ids)} fragments")


if __name__ == "__main__":
    main()
