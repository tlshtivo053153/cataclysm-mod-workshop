# CDDA Mod Development Framework

Naming (F-3): GitHub repo `cataclysm-mod-workshop`, pip package
`cdda-mod-framework` (`pyproject.toml`), working-copy dir
`cdda_mod_framework`. `README.md` uses the repo name; the package note there
is canonical for the pip name. (The plan file `cdda_mod_dev_plan.md` keeps its
historic name for the same reason noted in `README.md`.)

## Project Overview

This repository contains tools, scripts, and documentation for developing and porting mods for Cataclysm: Dark Days Ahead (CDDA).

## Key Files

- `cdda_mod_dev_plan.md` — Main development plan and workflow guide (Japanese)
- `rules/` — Knowledge base for mod development (CORE.md, common_errors.md, version_diff.md, hints_basic.md, verification.md, patterns/)
- `scripts/` — Validation and porting automation scripts (Python + Bash)
- `mods/` — Mod storage (small/medium/large/seen/unseen)
- `patches/` — Patch sets for porting old mods to new CDDA versions
- `templates/` — spec_template.md and design_template.md for mod design documents
- `external/cdda/` — CDDA game files (gitignored)
- `.github/workflows/ci.yml` — CI pipeline (ruff, black, pytest, mypy, shellcheck)

## Development Workflow (9 steps — canonical: `rules/CORE.md`)

New mod development follows the 9-step workflow. `rules/CORE.md` is canonical;
`README.md` and `cdda_mod_dev_plan.md` mirror it. Templates are used as follows:
`templates/spec_template.md` for Step 1, `templates/design_template.md` for Step 3.

1. Write a spec using `templates/spec_template.md` (skippable for small mods, see below)
2. Self-review the spec with AI (scope, conflicts with vanilla systems, fun/usefulness)
3. Write a design doc using `templates/design_template.md` (planned IDs, copy-from targets, dependencies)
4. Verify consistency against `external/cdda/data/json/` (copy-from IDs, flags, materials, activity_level)
5. Self-review the design doc with AI (naming, copy-from, dependencies, rework cost)
6. Implement (`modinfo.json`, `data/*.json`; run Level1 check on every edit)
7. Fix load errors (Level2: place mod then run `scripts/check_mods.sh`)
8. Verify in-game behavior (Level3: spawn/craft/effects vs success criteria)
9. Balance against same-category vanilla content (cost vs performance vs uniqueness)

Small-mod exemption (Steps 1–2 skippable only if ALL hold): 5 or fewer new
game IDs (excluding modinfo.json), `copy-from` only with no new `type`
definitions, extension of an existing system only (no new game systems,
mapgen, NPC logic, etc.), clearly derived from an existing same-category item.

## Old Mod Porting

Use the Python scripts in `scripts/` for mechanical transformations:
- `convert_item_types.py`
- `add_activity_level.py`
- `convert_price.py`
- `remove_armor_bullet.py`
- `remove_invalid_fields.py`
- `revert_all_translations.py` / `revert_translation_errors.py`
- `summarize_debug_log.py`

Then save the resulting diff as a patch set in `patches/`.

## Testing & Validation

- `bash scripts/validate.sh <mod_dir>` — JSON syntax check (Level1)
- `bash scripts/check_mods.sh <mod_name>` — CDDA engine load check (Level2)
- `bash scripts/place_mod_for_test.sh [--link|--copy] [--dry-run] [--force] <mod_dir>` — Symlink (default) or copy a mod into CDDA for testing (--force skips overwrite confirmation; `--link` is accepted as an explicit alias of the default)
- `.venv/bin/pytest scripts/tests/` — Run Python test suite
- `.venv/bin/ruff check scripts/` — Lint Python code
- `.venv/bin/mypy scripts/` — Type check Python code

## Mapgen DSL Subsystem

The `scripts/mapgen/` package provides a DSL compiler for CDDA mapgen JSON
(18 files: `ls scripts/mapgen/*.py | wc -l`):
- `mapgen/cli.py` — CLI entry point (`mapgen-compile`)
- `mapgen/compiler.py` — Main compiler entry point
- `mapgen/parser.py` — DSL parser
- `mapgen/schema.py` — JSON schema validation
- `mapgen/validation.py` — Map validation
- `mapgen/grid.py` — Grid layout processing
- `mapgen/room.py` — Room definitions
- `mapgen/stairs.py` — Stair placement
- `mapgen/walls.py` — Wall rendering
- `mapgen/doors.py` — Door placement
- `mapgen/placement.py` — Furniture/monster/item placement
- `mapgen/centering.py` — Grid centering
- `mapgen/builder.py` — Map assembly
- `mapgen/json_emitter.py` — JSON output
- `mapgen/constants.py` — Shared constants
- `mapgen/known_palettes.py` — Known palette registry (+ `palettes.json` data)
- `mapgen/utils.py` — Shared helpers
- `mapgen/__init__.py` — Package marker

## Rules

See `rules/CORE.md` for core development rules. Additional rule files are referenced from `cdda_mod_dev_plan.md`.

## Language

Language policy (F-3, Japanese-English coexistence): `AGENTS.md` stays in
English as the agent entry point; all other project docs (`README.md`,
`cdda_mod_dev_plan.md`, `rules/`) are canonically Japanese. Code comments,
CLI messages, and identifiers are English.

(Last verified: 2026-09-14 — bump when CORE.md workflow, verification levels,
naming, or CI contracts change; other doc-only fixes need not bump.)
