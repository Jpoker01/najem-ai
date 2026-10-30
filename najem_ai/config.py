"""Paths and constants shared by the ingest code. Paths are relative to the repo root."""

import os
import re
from pathlib import Path

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://najemai:najemai@localhost:5432/najemai",
)

RAW = Path("data/raw")
SCOPE = Path("data/scope.json")

# fragment types that hold citable text; Paragraf is only the "§ X" label,
# Nadpis_nad/Nadpis_pod are headings and Block_* are empty účinnost/přechodná blocks
TEXT_TYPES = {"Odstavec_Dc", "Pismeno_Lb", "Bod_Dd"}
LEVELS = ("par", "odst", "pism", "bod")
SEGMENT = re.compile(r"(par|odst|pism|bod)_(\w+)")
