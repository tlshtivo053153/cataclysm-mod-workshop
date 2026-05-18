#!/usr/bin/env python3
"""Convert numeric price/price_postapoc to string currency format for CDDA 0.I"""
import sys
import re
import json

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

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace price and price_postapoc numeric values
    def replace_price(match):
        key = match.group(1)
        val = int(match.group(2))
        return f'"{key}": "{format_price(val)}"'
    
    # Match "price": 123, or "price_postapoc": 123,
    # Be careful not to match already-string values
    content = re.sub(r'"(price|price_postapoc)":\s*(\d+)(\s*,?)', replace_price, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated: {filepath}")

if __name__ == "__main__":
    for path in sys.argv[1:]:
        process_file(path)
