#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "error: expected \$# == 1"
    exit 1
fi

MOD_ID="$1"

: > external/cdda/config/debug.log
cd external/cdda
timeout 30 ./cataclysm-tiles --check-mods "$MOD_ID" 2>&1 