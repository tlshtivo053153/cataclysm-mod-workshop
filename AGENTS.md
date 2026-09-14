# CDDA Mod Development Framework

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

## Development Workflow

1. Write a design document using `templates/design_template.md`
2. Implement with AI assistance
3. Run `bash scripts/validate.sh <mod_dir>` for JSON syntax checking
4. Test in-game (launch CDDA with the mod enabled)

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
- `bash scripts/place_mod_for_test.sh [--link|--copy] [--dry-run] [--force] <mod_dir>` — Symlink (default) or copy a mod into CDDA for testing (--force skips overwrite confirmation)
- `.venv/bin/pytest scripts/tests/` — Run Python test suite
- `.venv/bin/ruff check scripts/` — Lint Python code
- `.venv/bin/mypy scripts/` — Type check Python code

## Mapgen DSL Subsystem

The `scripts/mapgen/` package provides a DSL compiler for CDDA mapgen JSON:
- `mapgen/compiler.py` — Main compiler entry point
- `mapgen/parser.py` — DSL parser
- `mapgen/schema.py` — JSON schema validation
- `mapgen/grid.py` — Grid layout processing
- `mapgen/room.py` — Room definitions
- `mapgen/stairs.py` — Stair placement
    
## Rules

See `rules/CORE.md` for core development rules. Additional rule files are referenced from `cdda_mod_dev_plan.md`.

## Language

Project documentation is primarily in Japanese.

(Last verified: 2026-07-22)
