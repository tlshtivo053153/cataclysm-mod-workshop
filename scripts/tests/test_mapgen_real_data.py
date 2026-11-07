"""E2E test for the real DSL input (Phase 0).

shortcut: structural assertions only (entry count, size, om_terrain) —
upgrade to a golden parse comparison against data/mapgen/fortified_garage.json
once the YAML reproduces it byte-identically.
"""

from pathlib import Path

from mapgen.compiler import Compiler
from mapgen.parser import parse_dsl

MOD = Path(__file__).resolve().parents[2] / "mods" / "small" / "fortified_shelters"
YML = MOD / "data" / "mapgen_dsl" / "fortified_garage.yml"


class TestFortifiedGarageDsl:
    def test_compiles_three_entries_24x24(self):
        doc = parse_dsl(YML)
        entries = Compiler(
            palette_paths=[MOD / "data" / "palette"],
        ).compile(doc)
        assert [e.om_terrain for e in entries] == [
            "shelter_d",
            "shelter_d_roof",
            "shelter_d_under",
        ]
        for e in entries:
            rows = e.grid.to_rows()
            assert len(rows) == 24
            assert all(len(r) == 24 for r in rows)
