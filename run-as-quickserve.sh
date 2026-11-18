#!/bin/bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

clear

cd "$SCRIPT_DIR"

exec sudo -u quickserve \
    "$SCRIPT_DIR/.venv/bin/python" "$@"
