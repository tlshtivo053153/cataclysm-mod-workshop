#!/usr/bin/env python3
"""Convert numeric price/price_postapoc to string currency format for CDDA 0.I."""

import re
import shutil
import sys
from pathlib import Path

from common import backup_file, create_parser, resolve_paths


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


def process_file(input_path: Path, output_path: Path, backup: bool = True) -> bool:
    """Process a single JSON file using regex replacement."""
    try:
        with open(input_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {input_path}: {e}", file=sys.stderr)
        return False

    def replace_price(match):
        key = match.group(1)
        val = int(match.group(2))
        trailing = match.group(3)
        return f'"{key}": "{format_price(val)}"{trailing}'

    # Match "price": 123, or "price_postapoc": 123,
    new_content = re.sub(
        r'"(price|price_postapoc)":\s*(\d+)(\s*,?)',
        replace_price,
        content,
    )

    if new_content == content:
        return False  # No changes

    if backup and output_path == input_path:
        backup_file(input_path)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Updated: {output_path}")
    return True


def main():
    parser = create_parser("Convert numeric price fields to currency strings")
    args = parser.parse_args()
    input_path, output_path = resolve_paths(args)

    if input_path.is_dir():
        output_path.mkdir(parents=True, exist_ok=True)
        files = sorted(input_path.rglob("*.json"))
        success = 0
        for filepath in files:
            if output_path == input_path:
                if process_file(filepath, filepath, backup=args.backup):
                    success += 1
            else:
                dst = output_path / filepath.relative_to(input_path)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(filepath, dst)
                if process_file(dst, dst, backup=False):
                    success += 1
        print(f"Updated {success}/{len(files)} files.")
    else:
        if output_path != input_path and output_path.is_dir():
            output_path.mkdir(parents=True, exist_ok=True)
            dst = output_path / input_path.name
            shutil.copy2(input_path, dst)
            process_file(dst, dst, backup=False)
        else:
            process_file(input_path, output_path, backup=args.backup)


if __name__ == "__main__":
    main()
