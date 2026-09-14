#!/usr/bin/env python3
"""Summarize CDDA debug.log by grouping similar errors."""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Regex patterns
ERROR_START_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d+ ERROR")
TIMESTAMP_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.")
COLOR_START = "<color_white><color_cyan>"
COLOR_END = "</color>"


def parse_blocks(lines: list[str]) -> list[list[str]]:
    """Parse log lines into error blocks, merging backtrace continuations."""
    blocks: list[list[str]] = []
    current_block: list[str] | None = None

    for raw in lines:
        stripped = raw.rstrip("\n\r")

        if current_block is not None:
            # Backtrace continuation has no timestamp; merge it before the
            # timestamp split so the error message stays in the same block.
            if stripped.startswith("(continued from above) ERROR") and (
                "(error message will follow backtrace)" in current_block[0]
            ):
                current_block.append(stripped)
                continue
            if TIMESTAMP_RE.match(stripped):
                blocks.append(current_block)
                current_block = None
                # fall through to check if this line starts a new block
            else:
                current_block.append(stripped)
                continue

        if ERROR_START_RE.match(stripped):
            current_block = [stripped]

    if current_block is not None:
        blocks.append(current_block)

    return blocks


def extract_signature(block: list[str]) -> str:
    """Derive a normalized signature for an error block."""
    if not block:
        return "Unknown error"
    # 1. Backtrace error with continuation
    for line in block:
        if line.startswith("(continued from above) ERROR"):
            match = re.search(r"\] (.+)", line)
            if match:
                return match.group(1)
            return line

    block_text = "\n".join(block)
    first_line = block[0]

    # 2. Json-error blocks
    if "Json error:" in block_text:
        for line in block:
            start_idx = line.find(COLOR_START)
            if start_idx == -1:
                continue
            start_idx += len(COLOR_START)
            end_idx = line.find(COLOR_END, start_idx)
            msg = line[start_idx:end_idx] if end_idx != -1 else line[start_idx:]
            msg = msg.strip()

            if "flexbuffer_json.cpp" in first_line:
                # Normalize the quoted field name (first quoted string only)
                msg = re.sub(r'"[^"]*"', '"..."', msg, count=1)
                return msg

            if "text_style_check_reader.cpp" in first_line:
                # Normalize numbers for the "insufficient spaces" variant;
                # other variants have no numbers and pass through unchanged.
                if "insufficient spaces" in msg:
                    msg = re.sub(r"\d+", "...", msg)
                return msg

            if "translation.cpp" in first_line:
                return msg

            # Generic json-error fallback
            return msg

    # 3. Fallback: first non-empty line with timestamp removed
    for line in block:
        stripped = line.strip()
        if stripped:
            return re.sub(r"^\d{2}:\d{2}:\d{2}\.\d+\s+", "", stripped)

    return "Unknown error"


def summarize(blocks: list[list[str]]) -> dict[str, dict[str, Any]]:
    """Aggregate blocks by signature."""
    groups: dict[str, dict[str, Any]] = {}
    for block in blocks:
        sig = extract_signature(block)
        if sig not in groups:
            groups[sig] = {"count": 0, "example": block}
        groups[sig]["count"] += 1
    return groups


def format_human(groups: dict[str, dict[str, Any]], top: int | None = None) -> str:
    """Render human-readable summary."""
    if not groups:
        return "No errors found."

    items = sorted(groups.items(), key=lambda x: x[1]["count"], reverse=True)
    if top is not None:
        items = items[:top]

    lines: list[str] = []
    sep_major = "=" * 80
    sep_minor = "-" * 80

    for sig, info in items:
        lines.append(sep_major)
        lines.append(f"Count: {info['count']}")
        lines.append(f"Signature: {sig}")
        lines.append(sep_minor)
        lines.extend(info["example"])

    lines.append(sep_major)
    return "\n".join(lines)


def format_json(groups: dict[str, dict[str, Any]], top: int | None = None) -> str:
    """Render JSON summary."""
    items = sorted(groups.items(), key=lambda x: x[1]["count"], reverse=True)
    if top is not None:
        items = items[:top]

    output = []
    for sig, info in items:
        output.append(
            {
                "signature": sig,
                "count": info["count"],
                "example": info["example"],
            }
        )
    return json.dumps(output, indent=2, ensure_ascii=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize CDDA debug.log by grouping similar errors."
    )
    parser.add_argument("log", type=Path, help="Path to debug.log file")
    parser.add_argument(
        "--output", "-o", type=Path, default=None, help="Write summary to file instead of stdout"
    )
    parser.add_argument(
        "--top", "-n", type=int, default=None, help="Limit output to the N most frequent groups"
    )
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args()

    log_path: Path = args.log
    if not log_path.exists():
        print(f"File not found: {log_path}", file=sys.stderr)
        sys.exit(1)
    if not log_path.is_file():
        print(f"Not a file: {log_path}", file=sys.stderr)
        sys.exit(1)

    with log_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    blocks = parse_blocks(lines)
    groups = summarize(blocks)

    out = format_json(groups, top=args.top) if args.json else format_human(groups, top=args.top)

    if args.output is not None:
        args.output.write_text(out + "\n", encoding="utf-8")
    else:
        print(out)


if __name__ == "__main__":
    main()
