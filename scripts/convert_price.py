#!/usr/bin/env python3
"""Convert numeric price/price_postapoc to string currency format for CDDA 0.I."""

import sys
from pathlib import Path
from typing import Any

from common import MAX_RECURSION_DEPTH, run_standard_pipeline

MAX_DEPTH = MAX_RECURSION_DEPTH

PRICE_KEYS = frozenset({"price", "price_postapoc"})

# Numeric prices under these context keys are game-mechanics data (e.g.
# proportional/relative requirements, shopkeeper rules), not item values.
# They must stay numeric; convert_price leaves them unchanged with a warning.
# NOTE: "extend"/"delete" are intentionally included (conservative): mutation
# patches use these keys, and a price inside them is not a plain item value.
# If a future item patch legitimately needs conversion inside extend, handle
# it manually rather than loosening this guard.
NO_CONVERT_CONTEXTS = frozenset(
    {
        "proportional",
        "relative",
        "extend",
        "delete",
        "price_rules",
        "shopkeeper_price_rules",
    }
)


def format_price(value: int) -> str:
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


def _walk(node: Any, in_no_convert: bool, depth: int, src: Path) -> bool:
    """Recursively convert price fields in place. Returns True if changed."""
    if depth > MAX_DEPTH:
        if depth == MAX_DEPTH + 1:
            print(
                f"Warning: max recursion depth ({MAX_DEPTH}) exceeded in convert_price",
                file=sys.stderr,
            )
        return False
    changed = False
    if isinstance(node, dict):
        for key, value in list(node.items()):
            child_no_convert = in_no_convert or (key in NO_CONVERT_CONTEXTS) or key.startswith("//")
            if key in PRICE_KEYS:
                # bool is a subclass of int: exclude explicitly.
                if isinstance(value, bool):
                    continue
                if isinstance(value, int):
                    if in_no_convert:
                        print(
                            f"Warning: skipping price conversion in "
                            f"no-convert context in {src}: {key}={value}",
                            file=sys.stderr,
                        )
                        continue
                    if value < 0:
                        print(
                            f"Warning: leaving negative price unchanged "
                            f"in {src}: {key}={value}",
                            file=sys.stderr,
                        )
                        continue
                    node[key] = format_price(value)
                    changed = True
                    continue
                if isinstance(value, float):
                    print(
                        f"Warning: leaving non-int price unchanged " f"in {src}: {key}={value!r}",
                        file=sys.stderr,
                    )
                    continue
                if value is None:
                    print(
                        f"Warning: leaving null price unchanged in {src}: {key}=null",
                        file=sys.stderr,
                    )
                    continue
                if isinstance(value, (dict, list)) and _walk(
                    value, child_no_convert, depth + 1, src
                ):
                    changed = True
                continue
            if isinstance(value, (dict, list)) and _walk(value, child_no_convert, depth + 1, src):
                changed = True
    elif isinstance(node, list):
        for item in node:
            if isinstance(item, (dict, list)) and _walk(item, in_no_convert, depth + 1, src):
                changed = True
    return changed


def processor(data: Any, src: Path) -> Any | None:
    """Convert numeric prices; return None when nothing changed (skip)."""
    if not isinstance(data, (dict, list)):
        return None
    src_path = Path(src)
    if _walk(data, False, 0, src_path):
        return data
    return None


def main() -> int:
    return run_standard_pipeline(
        "Convert numeric price fields to currency strings",
        processor,
        copy_unchanged=True,
    )


if __name__ == "__main__":
    sys.exit(main())
