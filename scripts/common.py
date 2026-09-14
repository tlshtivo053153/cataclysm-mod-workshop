#!/usr/bin/env python3
"""Common utilities for CDDA mod transformation scripts."""

import argparse
import json
import os
import shutil
import stat
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MAX_RECURSION_DEPTH = 50


def _is_backup_path(base: Path, p: Path) -> bool:
    """Return True if p is under a `.bak` directory relative to base.

    Only the path relative to base is inspected.  Ancestors of base that
    happen to be named `.bak` do not cause exclusion, so a legitimate mod
    directory named `.bak` is never skipped wholesale — only its `.bak`
    children are excluded.
    """
    try:
        rel_parts = p.relative_to(base).parts
    except ValueError:
        return False
    return ".bak" in rel_parts


@dataclass
class ProcessResult:
    """Result of batch/single-file processing.

    Attributes:
        processed: Files where data was successfully transformed and saved.
        skipped: Files intentionally skipped (processor returned None).
        failed: Files where an error occurred.
    """

    processed: int = 0
    skipped: int = 0
    failed: int = 0

    @property
    def total(self) -> int:
        return self.processed + self.skipped + self.failed

    @property
    def has_errors(self) -> bool:
        return self.failed > 0


def revert_translation_field(value: Any) -> Any:
    """If value is a translation dict, return the original string; otherwise return value unchanged."""
    if isinstance(value, dict):
        for key in ("str_sp", "str"):
            if key in value:
                return value[key]
    return value


def create_parser(description: str) -> argparse.ArgumentParser:
    """Create a standard ArgumentParser with --input, --output, and --backup."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        type=Path,
        help="Input directory or file path to process",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output directory or file path (default: overwrite input)",
    )
    parser.add_argument(
        "--backup",
        "-b",
        action="store_true",
        default=True,
        help="Create .bak backup before overwriting (default: True)",
    )
    parser.add_argument(
        "--no-backup",
        dest="backup",
        action="store_false",
        help="Disable backup creation",
    )
    return parser


def resolve_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    """Resolve input and output paths from parsed args.

    Returns (input_path, output_path). If --output is omitted, output_path == input_path.
    """
    input_path = args.input.resolve()
    output_path = input_path if args.output is None else args.output.resolve()
    return input_path, output_path


def backup_file(source: Path, backup_dir: Path | None = None) -> Path:
    """Copy source file to a .bak directory.

    If backup_dir is None, uses <source.parent>/.bak.
    Generations: the bare name is the oldest generation, then `.1`, `.2`, ...
    in increasing newness (first existing name wins, then suffixed copies).
    Callers only create backups when overwriting in place
    (`output_dir == input_dir`); a different output tree never backs up.
    Returns the path to the backup file.
    """
    if backup_dir is None:
        backup_dir = source.parent / ".bak"
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_path = backup_dir / source.name
    counter = 1
    while backup_path.exists():
        backup_path = backup_dir / f"{source.name}.{counter}"
        counter += 1

    if source.is_dir():
        shutil.copytree(source, backup_path, dirs_exist_ok=True)
    else:
        shutil.copy2(source, backup_path)
    return backup_path


def load_json(path: Path) -> list[Any] | dict[str, Any]:
    """Load JSON from path with descriptive error messages."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)  # type: ignore[no-any-return]
    except json.JSONDecodeError as e:
        print(f"JSON parse error in {path}: {e}", file=sys.stderr)
        raise
    except FileNotFoundError:
        print(f"File not found: {path}", file=sys.stderr)
        raise


def save_json(path: Path, data: list[Any] | dict[str, Any], indent: int = 4) -> None:
    """Save JSON to path with consistent formatting (atomic write via temp file)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path_str = tempfile.mkstemp(dir=path.parent, suffix=".tmp", prefix=path.stem)
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
            f.write("\n")
        os.chmod(tmp_path, stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644)
        tmp_path.replace(path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def process_directory(
    input_dir: Path,
    output_dir: Path,
    processor: Callable[..., Any],
    backup: bool = True,
    pattern: str = "*.json",
) -> ProcessResult:
    """Walk input_dir, apply processor to each matching file, write to output_dir.

    processor receives (data: list|dict, file_path: Path) and should return:
      - transformed data (list|dict) to save the file
      - None to skip the file (intentional no-op)

    Returns a ProcessResult with counts for processed, skipped, and failed files.

    `.bak` directories under input_dir are excluded from the walk (see
    _is_backup_path).  Backups are only created when overwriting in place
    (output_dir == input_dir).
    """
    result = ProcessResult()

    if not input_dir.exists():
        print(f"Directory not found: {input_dir}", file=sys.stderr)
        return result

    files = sorted(p for p in input_dir.rglob(pattern) if not _is_backup_path(input_dir, p))

    for src in files:
        try:
            data = load_json(src)
            transformed = processor(data, src)
            if transformed is None:
                result.skipped += 1
                continue

            dst = src if output_dir == input_dir else output_dir / src.relative_to(input_dir)

            if backup and dst == src:
                backup_file(src)

            save_json(dst, transformed)
            print(f"Updated: {dst}")
            result.processed += 1
        except Exception as e:
            print(f"Error processing {src}: {e}", file=sys.stderr)
            result.failed += 1

    if result.failed > 0:
        print(
            f"Processed {result.processed}, skipped {result.skipped}, " f"failed {result.failed}",
            file=sys.stderr,
        )

    return result


def process_file(
    input_path: Path,
    output_path: Path,
    processor: Callable[..., Any],
    backup: bool = True,
) -> ProcessResult:
    """Apply processor to a single file and write result.

    Returns a ProcessResult.  On error the result has failed=1.
    A processor returning None is treated as an intentional skip (skipped=1).
    """
    result = ProcessResult()
    try:
        data = load_json(input_path)
        transformed = processor(data, input_path)
        if transformed is None:
            result.skipped = 1
            return result

        if backup and output_path == input_path:
            backup_file(input_path)

        save_json(output_path, transformed)
        print(f"Updated: {output_path}")
        result.processed = 1
        return result
    except Exception as e:
        print(f"Error processing {input_path}: {e}", file=sys.stderr)
        result.failed = 1
        return result


def run_standard_pipeline(description: str, processor: Callable[..., Any]) -> None:
    """Run a standard input/output pipeline for a transformation script.

    Handles argument parsing, path resolution, and dispatches to
    process_directory() or process_file() based on whether the input
    is a directory or a single file.

    Exit codes:
        0 - all files processed successfully (including intentional skips)
        1 - one or more files failed processing
    """
    parser = create_parser(description)
    args = parser.parse_args()
    input_path, output_path = resolve_paths(args)

    if input_path.is_dir():
        result = process_directory(input_path, output_path, processor, backup=args.backup)
        print(
            f"Updated {result.processed} files, skipped {result.skipped}, "
            f"failed {result.failed}."
        )
    else:
        result = process_file(input_path, output_path, processor, backup=args.backup)
        if result.skipped:
            print(f"Skipped: {input_path}")
        elif result.processed:
            print(f"Updated: {input_path}")

    if result.has_errors:
        sys.exit(1)
