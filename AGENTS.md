# CDDA Mod Development Framework

## Project Overview

This repository contains tools, scripts, and documentation for developing and porting mods for Cataclysm: Dark Days Ahead (CDDA).

## Key Files

- `cdda_mod_dev_plan.md` — Main development plan and workflow guide (Japanese)
- `rules/` — Knowledge base for mod development (CORE.md, common_errors.md, version_diff.md, hints_basic.md)
- `scripts/` — Validation and porting automation scripts
- `mods/` — Mod storage (small/medium/large/seen/unseen)
- `patches/` — Patch sets for porting old mods to new CDDA versions
- `templates/` — design_template.md for mod design documents
- `external/cdda/` — CDDA game files (gitignored)

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

Then save the resulting diff as a patch set in `patches/`.

## Rules

See `rules/CORE.md` for core development rules. Additional rule files are referenced from `cdda_mod_dev_plan.md`.

## Language

Project documentation is primarily in Japanese.
