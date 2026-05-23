#!/usr/bin/env python3
"""Common utilities for CDDA mod transformation scripts."""

import argparse
import json
import shutil
import sys
from pathlib import Path


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
    Returns the path to the backup file.
    """
    if backup_dir is None:
        backup_dir = source.parent / ".bak"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Preserve relative structure when backing up directories
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


def load_json(path: Path) -> list | dict:
    """Load JSON from path with descriptive error messages."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSON parse error in {path}: {e}", file=sys.stderr)
        raise
    except FileNotFoundError:
        print(f"File not found: {path}", file=sys.stderr)
        raise


def save_json(path: Path, data: list | dict, indent: int = 4) -> None:
    """Save JSON to path with consistent formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
        f.write("\n")


def process_directory(
    input_dir: Path,
    output_dir: Path,
    processor: callable,
    backup: bool = True,
    pattern: str = "*.json",
) -> int:
    """Walk input_dir, apply processor to each matching file, write to output_dir.

    processor receives (data: list|dict, file_path: Path) and should return
    the transformed data.  If processor returns None, the file is skipped.

    Returns the number of successfully processed files.
    """
    if not input_dir.exists():
        print(f"Directory not found: {input_dir}", file=sys.stderr)
        sys.exit(1)

    files = sorted(input_dir.rglob(pattern))
    success = 0
    for src in files:
        try:
            data = load_json(src)
            transformed = processor(data, src)
            if transformed is None:
                continue

            dst = src if output_dir == input_dir else output_dir / src.relative_to(input_dir)

            if backup and dst == src:
                backup_file(src)

            save_json(dst, transformed)
            print(f"Updated: {dst}")
            success += 1
        except Exception as e:
            print(f"Error processing {src}: {e}", file=sys.stderr)

    return success


def process_file(
    input_path: Path,
    output_path: Path,
    processor: callable,
    backup: bool = True,
) -> bool:
    """Apply processor to a single file and write result.

    Returns True on success.
    """
    try:
        data = load_json(input_path)
        transformed = processor(data, input_path)
        if transformed is None:
            return False

        if backup and output_path == input_path:
            backup_file(input_path)

        save_json(output_path, transformed)
        print(f"Updated: {output_path}")
        return True
    except Exception as e:
        print(f"Error processing {input_path}: {e}", file=sys.stderr)
        return False


def run_standard_pipeline(description: str, processor: callable) -> None:
    """Run a standard input/output pipeline for a transformation script.

    Handles argument parsing, path resolution, and dispatches to
    process_directory() or process_file() based on whether the input
    is a directory or a single file.
    """
    parser = create_parser(description)
    args = parser.parse_args()
    input_path, output_path = resolve_paths(args)

    if input_path.is_dir():
        count = process_directory(input_path, output_path, processor, backup=args.backup)
        print(f"Updated {count} files.")
    else:
        process_file(input_path, output_path, processor, backup=args.backup)
