#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=. python scripts/validate_packs.py
PYTHONPATH=. pytest backend/tests -q
