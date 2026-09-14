#!/usr/bin/env python3
"""Common utilities for CDDA mod transformation scripts.

Import policy (B-2): absolute imports from the scripts/ root.
Top-level modules use ``from common import ...``; the mapgen subpackage
uses ``from mapgen.<module> import ...`` (never relative ``from .`` or
``from scripts.``). The dist maps scripts/ via
``[tool.setuptools] package-dir = {"" = "scripts"}`` (py-modules +
``mapgen*`` package); source runs resolve the same root via pytest
``pythonpath = ["scripts"]`` or ``cwd=scripts``. No per-file
``sys.path.insert`` hacks.
"""

import argparse
import copy
import json
import os
import shutil
import stat
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

# Processor signature shared by all JSON pipeline scripts:
# (data, source_path) -> transformed data or None (skip).
Processor = Callable[[Any, Path], list[Any] | dict[str, Any] | None]
# Setup hook signature: (parsed args) -> exit code to abort, or None to continue.
SetupHook = Callable[[argparse.Namespace], int | None]
# Parser configuration hook.
ConfigureHook = Callable[[argparse.ArgumentParser], None]

MAX_RECURSION_DEPTH = 50


def depth_exceeded(depth: int, script: str) -> bool:
    """Return True if recursion depth exceeds MAX_RECURSION_DEPTH (E-3).

    Warns once on stderr when depth == MAX_RECURSION_DEPTH + 1, then stays
    silent for deeper levels. Callers return the current node unchanged
    when this returns True.
    """
    if depth > MAX_RECURSION_DEPTH:
        if depth == MAX_RECURSION_DEPTH + 1:
            print(
                f"Warning: max recursion depth ({MAX_RECURSION_DEPTH}) exceeded in {script}",
                file=sys.stderr,
            )
        return True
    return False


def snapshot(data: Any) -> Any:
    """Deep-copy JSON data for no-op comparison (E-3)."""
    return copy.deepcopy(data)


def is_unchanged(original: Any, current: Any) -> bool:
    """Return True when a transform left data unchanged (E-3)."""
    return bool(original == current)


def noop_if_unchanged(original: Any, result: Any) -> Any | None:
    """Return None (skip) when result equals original, else result (E-3)."""
    if is_unchanged(original, result):
        return None
    return result


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
    """If value is a translation dict, return the original string; otherwise return value unchanged.

    Only string extractions are returned (empty string included); e.g.
    {"str": None} is kept as-is instead of propagating None into
    name/description.
    """
    if isinstance(value, dict):
        for key in ("str_sp", "str"):
            if key in value and isinstance(value[key], str):
                return value[key]
    return value


def create_parser(
    description: str,
    configure: ConfigureHook | None = None,
) -> argparse.ArgumentParser:
    """Create a standard ArgumentParser with --input, --output, and --backup.

    Args:
        description: Help text shown for the script.
        configure: Optional hook to register script-specific options
            (e.g. add_activity_level --config). Called with the parser
            before it is returned so ``--help`` lists standard options
            first and extra options last.
    """
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
    if configure is not None:
        configure(parser)
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
            return cast(list[Any] | dict[str, Any], json.load(f))
    except json.JSONDecodeError as e:
        print(f"JSON parse error in {path}: {e}", file=sys.stderr)
        raise
    except FileNotFoundError:
        print(f"File not found: {path}", file=sys.stderr)
        raise
    except UnicodeDecodeError as e:
        print(f"ERROR: Cannot decode {path} as UTF-8: {e}", file=sys.stderr)
        raise
    except OSError as e:
        print(f"ERROR: Cannot read {path}: {e}", file=sys.stderr)
        raise


def save_json(path: Path, data: list[Any] | dict[str, Any], indent: int = 4) -> None:
    """Save JSON to path with consistent formatting (atomic write via temp file).

    Symlink-preserving: if *path* is a symlink, the target file is replaced
    instead of the link itself, so ``place_mod_for_test.sh`` symlink setups
    survive converter runs.  The write is still atomic (temp file in the
    target directory + os.replace).
    """
    # Resolve symlink target first so tmp+replace happens in the real dir.
    target = path
    try:
        if path.is_symlink():
            target = path.resolve(strict=False)
    except Exception:
        target = path
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path_str = tempfile.mkstemp(dir=target.parent, suffix=".tmp", prefix=target.stem)
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
            f.write("\n")
        if target.exists():
            os.chmod(tmp_path, stat.S_IMODE(target.stat().st_mode))
        else:
            # Respect umask for new files (old open(path, "w") behavior).
            current_umask = os.umask(0)
            os.umask(current_umask)
            os.chmod(tmp_path, 0o666 & ~current_umask)
        tmp_path.replace(target)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def process_directory(
    input_dir: Path,
    output_dir: Path,
    processor: Processor,
    backup: bool = True,
    pattern: str = "*.json",
    copy_unchanged: bool = False,
) -> ProcessResult:
    """Walk input_dir, apply processor to each matching file, write to output_dir.

    processor receives (data: list|dict, file_path: Path) and should return:
      - transformed data (list|dict) to save the file
      - None to skip the file (intentional no-op)

    Returns a ProcessResult with counts for processed, skipped, and failed files.

    `.bak` directories under input_dir are excluded from the walk (see
    _is_backup_path).  Backups are only created when overwriting in place
    (output_dir == input_dir).

    When output_dir differs and copy_unchanged is True, files the processor
    skips (None) are still copied to the output tree (failed files are not).
    This preserves the `-o <other-dir>` full-copy contract for scripts that
    need it (e.g. convert_price).  Other scripts keep False (in-place
    behavior unchanged).

    NOTE: with copy_unchanged=False (default), `-o <other-dir>` produces a
    partial tree: unchanged (skipped) files are NOT copied.  Use in-place
    mode or convert_price for full-copy needs.

    Missing input_dir counts as failed=1 (not silent success).  Mutually
    nested input/output dirs (one contains the other) are rejected with
    failed=1 to prevent recursive self-growth (e.g. `-o <input>/out`).
    """
    result = ProcessResult()

    if not input_dir.exists():
        print(f"Directory not found: {input_dir}", file=sys.stderr)
        result.failed = 1
        return result

    try:
        input_res = input_dir.resolve()
        output_res = output_dir.resolve()
    except Exception:
        input_res = input_dir
        output_res = output_dir
    if output_res != input_res:
        try:
            nested = output_res.is_relative_to(input_res) or input_res.is_relative_to(output_res)
        except Exception:
            nested = False
        if nested:
            print(
                f"Error: input and output directories must not contain each other: "
                f"{input_dir} vs {output_dir}",
                file=sys.stderr,
            )
            result.failed = 1
            return result

    files = sorted(p for p in input_dir.rglob(pattern) if not _is_backup_path(input_dir, p))

    for src in files:
        try:
            data = load_json(src)
            transformed = processor(data, src)
            if transformed is None:
                if copy_unchanged and output_res != input_res:
                    try:
                        dst = output_dir / src.relative_to(input_dir)
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
                    except Exception as e:
                        print(f"Error copying {src}: {e}", file=sys.stderr)
                        result.failed += 1
                        continue
                result.skipped += 1
                continue

            dst = src if output_res == input_res else output_dir / src.relative_to(input_dir)

            if backup and output_res == input_res:
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

    if output_res != input_res and not copy_unchanged and result.skipped > 0:
        print(
            f"Warning: {result.skipped} unchanged file(s) not copied to {output_dir} "
            "(copy_unchanged=False produces a partial tree; use in-place mode "
            "or a full-copy script for complete output)",
            file=sys.stderr,
        )

    return result


def process_file(
    input_path: Path,
    output_path: Path,
    processor: Processor,
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

        try:
            same_file = output_path.resolve() == input_path.resolve()
        except (OSError, RuntimeError):
            same_file = output_path == input_path
        if backup and same_file:
            backup_file(input_path)

        save_json(output_path, transformed)
        print(f"Updated: {output_path}")
        result.processed = 1
        return result
    except Exception as e:
        print(f"Error processing {input_path}: {e}", file=sys.stderr)
        result.failed = 1
        return result


def _setup_exit_code(setup_code: Any) -> int | None:
    """Decide whether a setup hook return value aborts the pipeline.

    Fail-closed: only None (continue) and int 0 (continue) proceed.
    Any other value — non-zero int, bool (incl. False), or off-type
    (str/float) — aborts with the code, or 1 for off-type values.
    `setup` is typed int|None; bool/str are runtime contract violations.
    """
    if setup_code is None:
        return None
    if type(setup_code) is int:
        return None if setup_code == 0 else setup_code
    print(f"ERROR: invalid setup exit code: {setup_code!r}", file=sys.stderr)
    return 1


def run_standard_pipeline(
    description: str,
    processor: Processor,
    copy_unchanged: bool = False,
    configure: ConfigureHook | None = None,
    setup: SetupHook | None = None,
) -> int:
    """Run a standard input/output pipeline for a transformation script.

    Handles argument parsing, path resolution, and dispatches to
    process_directory() or process_file() based on whether the input
    is a directory or a single file.

    Single-file input with an existing directory as output is saved as
    <output_dir>/<input_name> (legacy convert_price contract). All
    run_standard_pipeline users share this rescue; do not reimplement
    per-script dispatch.

    Args:
        description: Help text for --help.
        processor: (data, path) -> transformed data or None (skip).
        copy_unchanged: Forward to process_directory() for `-o <other-dir>`
            full-copy needs (convert_price=True, others False).
        configure: Optional create_parser hook for script-specific options.
        setup: Optional hook run after parse_args (e.g. load --config).
            May return an int exit code to abort before processing
            (e.g. missing config -> 1); None means continue.

    Returns:
        Exit code following the unified CLI policy (E-1): 0 success,
        1 processing error. Usage errors (missing required args) exit 2
        via argparse before this returns. Callers use
        ``def main() -> int: return run_standard_pipeline(...)`` with
        ``sys.exit(main())``.

    Exit codes (all Python CLIs):
        0 - all files processed successfully (including intentional skips)
        1 - one or more files failed processing (incl. missing input,
            nested input/output, missing config)
        2 - usage error (argparse; mapgen also uses 2 for missing
            input/DSL dir and no-input cases)

    Divergence note (mapgen/cli.py stays separate): the mapgen DSL compiler
    does not use this pipeline because its inputs are YAML (not JSON),
    it supports --mod-dir batch mode with a fixed data/mapgen output tree,
    --check-only (validate without writing), --palette-dir/--explain, and
    exit 2 for usage errors (missing input/DSL dir) vs exit 1 for
    processing errors. It shares only backup_file()/save_json() with this
    module. Keep this divergence intentional; do not force mapgen onto
    the JSON directory/file pipeline.
    """
    parser = create_parser(description, configure=configure)
    args = parser.parse_args()
    if setup is not None:
        abort = _setup_exit_code(setup(args))
        if abort is not None:
            return abort
    input_path, output_path = resolve_paths(args)

    if input_path.is_dir():
        result = process_directory(
            input_path, output_path, processor, backup=args.backup, copy_unchanged=copy_unchanged
        )
        print(
            f"Updated {result.processed} files, skipped {result.skipped}, "
            f"failed {result.failed}."
        )
    else:
        if output_path.is_dir():
            output_path = output_path / input_path.name
        result = process_file(input_path, output_path, processor, backup=args.backup)
        if result.skipped:
            print(f"Skipped: {input_path}")
        elif result.processed:
            print(f"Updated: {input_path}")

    if result.has_errors:
        return 1
    return 0
