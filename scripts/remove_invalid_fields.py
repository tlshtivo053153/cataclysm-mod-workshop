#!/usr/bin/env python3
"""Remove invalid JSON fields from CDDA mod files."""

import json
import sys
from pathlib import Path

from common import create_parser, process_directory, process_file, resolve_paths

# Resolve invalid_fields.json relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INVALID_FIELDS_PATH = PROJECT_ROOT / "rules" / "invalid_fields.json"


def load_invalid_fields() -> set[str]:
    """Load the set of invalid field names from rules/invalid_fields.json."""
    with open(INVALID_FIELDS_PATH, encoding="utf-8") as f:
        fields = json.load(f)
    return set(fields)


def remove_invalid_fields(obj, invalid_fields: set[str]):
    """Recursively remove invalid fields from a JSON object."""
    if isinstance(obj, dict):
        keys_to_remove = [k for k in obj if k in invalid_fields]
        for k in keys_to_remove:
            del obj[k]
        for v in obj.values():
            remove_invalid_fields(v, invalid_fields)
    elif isinstance(obj, list):
        for item in obj:
            remove_invalid_fields(item, invalid_fields)
    return obj


def make_processor(invalid_fields: set[str]):
    def processor(data, _path):
        if isinstance(data, list):
            for item in data:
                remove_invalid_fields(item, invalid_fields)
        elif isinstance(data, dict):
            remove_invalid_fields(data, invalid_fields)
        return data

    return processor


def main():
    parser = create_parser("Remove invalid JSON fields from CDDA mod files")
    args = parser.parse_args()

    if not INVALID_FIELDS_PATH.exists():
        print(f"Invalid fields list not found: {INVALID_FIELDS_PATH}", file=sys.stderr)
        sys.exit(1)

    invalid_fields = load_invalid_fields()
    input_path, output_path = resolve_paths(args)

    if input_path.is_dir():
        count = process_directory(input_path, output_path, make_processor(invalid_fields), backup=args.backup)
        print(f"Updated {count} files.")
    else:
        process_file(input_path, output_path, make_processor(invalid_fields), backup=args.backup)


if __name__ == "__main__":
    main()
