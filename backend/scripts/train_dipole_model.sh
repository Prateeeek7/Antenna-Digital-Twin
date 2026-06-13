#!/usr/bin/env bash
set -euo pipefail

# Train a dipole-specific surrogate model set without deleting existing models.
# Usage:
#   ./backend/scripts/train_dipole_model.sh /path/to/dipole_data.json
#   ./backend/scripts/train_dipole_model.sh               # defaults to backend/dipole/results/Old_custom_dipole_results.json

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
JSON_PATH="${1:-backend/dipole/results/Old_custom_dipole_results.json}"

cd "$ROOT_DIR"
PYTHONPATH="$ROOT_DIR" python backend/scripts/train_surrogate_model.py \
  --dipole-json "$JSON_PATH" \
  --model-name dipole
