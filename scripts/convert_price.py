#!/usr/bin/env python3
"""Convert numeric price/price_postapoc to string currency format for CDDA 0.I."""

import re
import shutil
import sys
from pathlib import Path

from common import ProcessResult, backup_file, create_parser, resolve_paths


def format_price(value):
    """Convert cent value to currency string."""
    if value == 0:
        return "0 cent"
    cents = value % 100
    dollars = value // 100

    if dollars == 0:
        return f"{cents} cent"

    parts = []
    if dollars >= 1000:
        k = dollars // 1000
        rem = dollars % 1000
        parts.append(f"{k} kUSD")
        if rem > 0:
            parts.append(f"{rem} USD")
    else:
        parts.append(f"{dollars} USD")

    if cents > 0:
        parts.append(f"{cents} cent")

    return " ".join(parts)


def process_file(input_path: Path, output_path: Path, backup: bool = True) -> ProcessResult:
    """Process a single JSON file using regex replacement."""
    result = ProcessResult()
    try:
        with open(input_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {input_path}: {e}", file=sys.stderr)
        result.failed = 1
        return result

    def replace_price(match):
        key = match.group(1)
        val = int(match.group(2))
        trailing = match.group(3)
        return f'"{key}": "{format_price(val)}"{trailing}'

    new_content = re.sub(
        r'"(price|price_postapoc)":\s*(\d+)(\s*,?)',
        replace_price,
        content,
    )

    if new_content == content:
        result.skipped = 1
        return result

    if backup and output_path == input_path:
        backup_file(input_path)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Updated: {output_path}")
    result.processed = 1
    return result


def main():
    parser = create_parser("Convert numeric price fields to currency strings")
    args = parser.parse_args()
    input_path, output_path = resolve_paths(args)

    total = ProcessResult()

    if input_path.is_dir():
        output_path.mkdir(parents=True, exist_ok=True)
        files = sorted(input_path.rglob("*.json"))
        for filepath in files:
            if output_path == input_path:
                r = process_file(filepath, filepath, backup=args.backup)
            else:
                dst = output_path / filepath.relative_to(input_path)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(filepath, dst)
                r = process_file(dst, dst, backup=False)
            total.processed += r.processed
            total.skipped += r.skipped
            total.failed += r.failed
    else:
        if output_path != input_path and output_path.is_dir():
            output_path.mkdir(parents=True, exist_ok=True)
            dst = output_path / input_path.name
            shutil.copy2(input_path, dst)
            total = process_file(dst, dst, backup=False)
        else:
            total = process_file(input_path, output_path, backup=args.backup)

    print(f"Updated {total.processed} files, skipped {total.skipped}, " f"failed {total.failed}.")

    if total.has_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
