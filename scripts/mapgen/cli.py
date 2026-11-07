"""Command-line entry point for the mapgen DSL compiler."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import yaml
from common import backup_file, save_json

from mapgen import CompileError, EntryContext
from mapgen.compiler import Compiler
from mapgen.parser import parse_dsl
from mapgen.schema import DSLDocument, EntrySpec


def _print_warnings(entries: list[EntryContext]) -> None:
    for entry in entries:
        for w in entry.warnings:
            print(f"WARNING [{w.code}] {entry.om_terrain}: {w.message}", file=sys.stderr)


def _print_explanations(
    compiler: Compiler,
    entries: list[EntryContext],
    doc_entries: list[EntrySpec],
) -> None:
    for entry, spec in zip(entries, doc_entries, strict=True):
        for line in compiler.explain_chars(entry, features=spec.features):
            print(line)


def _write_output(
    output_path: Path,
    data: list[dict[str, Any]],
    backup: bool,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if backup and output_path.exists():
        backup_file(output_path)
    save_json(output_path, data)
    print(f"Compiled: {output_path}")


def _compile_doc(
    compiler: Compiler,
    yaml_path: Path,
) -> tuple[DSLDocument, list[EntryContext], list[dict[str, Any]]] | None:
    """Parse + compile a single YAML, returning (doc, entries, emitted) or None on error."""
    try:
        doc = parse_dsl(yaml_path)
        entries = compiler.compile(doc)
    except yaml.YAMLError as e:
        print(f"YAML syntax error in {yaml_path}: {e}", file=sys.stderr)
        return None
    except CompileError as e:
        print(f"Compile error in {yaml_path}: {e}", file=sys.stderr)
        return None
    except PermissionError as e:
        print(f"ERROR: Permission denied reading {yaml_path}: {e}", file=sys.stderr)
        return None
    except UnicodeDecodeError as e:
        print(f"ERROR: Cannot decode {yaml_path} as UTF-8: {e}", file=sys.stderr)
        return None
    except OSError as e:
        print(f"ERROR: Cannot read {yaml_path}: {e}", file=sys.stderr)
        return None
    return doc, entries, compiler.emit(entries)


def _run_single_file(
    input_path: Path,
    output_path: Path | None,
    backup: bool,
    check_only: bool,
    palette_paths: list[Path],
    explain: bool = False,
) -> int:
    if not input_path.exists():
        print(f"File not found: {input_path}", file=sys.stderr)
        return 2
    if not input_path.is_file():
        print(f"Not a file: {input_path}", file=sys.stderr)
        return 2

    try:
        compiler = Compiler(palette_paths=palette_paths if palette_paths else None)
    except PermissionError as e:
        print(f"ERROR: Permission denied loading palettes: {e}", file=sys.stderr)
        return 1
    except UnicodeDecodeError as e:
        print(f"ERROR: Cannot decode palette as UTF-8: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"ERROR: Cannot load palettes: {e}", file=sys.stderr)
        return 1
    compiled = _compile_doc(compiler, input_path)
    if compiled is None:
        return 1
    doc, entries, data = compiled

    _print_warnings(entries)
    if explain:
        _print_explanations(compiler, entries, doc.entries)

    if not check_only:
        if output_path is None:
            output_path = input_path.with_suffix(".json")
        _write_output(output_path, data, backup)
    return 0


def _run_mod_dir(
    mod_dir: Path,
    dsl_dir: str,
    backup: bool,
    check_only: bool,
    palette_paths: list[Path],
    explain: bool = False,
) -> int:
    dsl_path = mod_dir / dsl_dir
    if not dsl_path.exists():
        print(f"DSL directory not found: {dsl_path}", file=sys.stderr)
        return 2

    compiler: Compiler
    try:
        compiler = Compiler(palette_paths=palette_paths if palette_paths else None)
    except PermissionError as e:
        print(f"ERROR: Permission denied loading palettes: {e}", file=sys.stderr)
        return 1
    except UnicodeDecodeError as e:
        print(f"ERROR: Cannot decode palette as UTF-8: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"ERROR: Cannot load palettes: {e}", file=sys.stderr)
        return 1
    yaml_files = sorted(dsl_path.glob("*.yml"))
    compiled_count = 0
    error_count = 0
    output_dir = mod_dir / "data" / "mapgen"

    for yml_file in yaml_files:
        try:
            doc = parse_dsl(yml_file)
            entries = compiler.compile(doc)
        except yaml.YAMLError as e:
            print(f"YAML syntax error in {yml_file}: {e}", file=sys.stderr)
            error_count += 1
            continue
        except CompileError as e:
            print(f"Compile error in {yml_file}: {e}", file=sys.stderr)
            error_count += 1
            continue
        except PermissionError as e:
            print(f"ERROR: Permission denied reading {yml_file}: {e}", file=sys.stderr)
            error_count += 1
            continue
        except UnicodeDecodeError as e:
            print(f"ERROR: Cannot decode {yml_file} as UTF-8: {e}", file=sys.stderr)
            error_count += 1
            continue
        except OSError as e:
            print(f"ERROR: Cannot read {yml_file}: {e}", file=sys.stderr)
            error_count += 1
            continue

        data = compiler.emit(entries)
        _print_warnings(entries)
        if explain:
            _print_explanations(compiler, entries, doc.entries)

        if not check_only:
            _write_output(output_dir / f"{yml_file.stem}.json", data, backup)
            compiled_count += 1

    if check_only:
        print(f"Checked {len(yaml_files)} files, {error_count} errors")
    else:
        print(f"Compiled {compiled_count} files, {error_count} errors")
    if error_count > 0:
        return 1
    return 0


def main() -> int:
    """Mapgen DSL compiler entry point.

    Returns unified exit codes (E-1): 0 success, 1 processing error
    (YAML/compile failures), 2 usage error (no --input/--mod-dir,
    missing input file or DSL dir). Use ``sys.exit(main())``.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Mapgen DSL compiler for CDDA")
    parser.add_argument("--input", "-i", type=Path, help="Input YAML file")
    parser.add_argument("--output", "-o", type=Path, help="Output JSON file")
    parser.add_argument("--check-only", action="store_true", help="Validate only, no file output")
    parser.add_argument("--mod-dir", type=Path, help="Mod directory for batch compilation")
    parser.add_argument(
        "--dsl-dir",
        type=str,
        default="data/mapgen_dsl",
        help="DSL source directory within mod-dir (default: data/mapgen_dsl)",
    )
    parser.add_argument(
        "--palette-dir",
        type=Path,
        nargs="*",
        default=None,
        help="Additional palette directory(s) to load",
    )
    parser.add_argument(
        "--no-backup",
        dest="backup",
        action="store_false",
        default=True,
        help="Disable backup creation",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Show palette character meanings used in the compiled map",
    )

    args = parser.parse_args()

    palette_paths: list[Path] = list(args.palette_dir) if args.palette_dir else []

    if args.mod_dir:
        for dirname in ("data/palettes", "data/palette"):
            auto_palette = args.mod_dir / dirname
            if auto_palette.is_dir() and auto_palette not in palette_paths:
                palette_paths.append(auto_palette)
        return _run_mod_dir(
            args.mod_dir, args.dsl_dir, args.backup, args.check_only, palette_paths, args.explain
        )
    elif args.input:
        return _run_single_file(
            args.input, args.output, args.backup, args.check_only, palette_paths, args.explain
        )
    else:
        parser.print_help()
        return 2


if __name__ == "__main__":
    sys.exit(main())
