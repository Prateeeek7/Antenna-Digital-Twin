#!/usr/bin/env bash
# Antenna Digital Twin – single script for all run commands
# Usage: ./run_engine.sh [backend|frontend|train|all]

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR"
PYTHONPATH="${ROOT}:${PYTHONPATH:-}"

# Use project venv if present (e.g. after scripts/install_openems_here.sh)
if [ -d "$ROOT/.venv" ]; then
  PYTHON="${ROOT}/.venv/bin/python"
else
  PYTHON=python3
fi

# Optional: add openEMS Python modules from another install (see docs/OPENEMS_SETUP.md)
[ -f "$ROOT/.env" ] && set -a && . "$ROOT/.env" && set +a
if [ -n "${OPENEMS_PYTHON_PATH:-}" ]; then
  export PYTHONPATH="${OPENEMS_PYTHON_PATH}:${PYTHONPATH}"
fi

run_backend() {
  echo "Starting backend (uvicorn) on http://0.0.0.0:8000 ..."
  cd "$ROOT/backend"
  export PYTHONPATH="$ROOT:$PYTHONPATH"
  exec "$PYTHON" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
}

run_frontend() {
  echo "Starting frontend (Vite) ..."
  cd "$ROOT/frontend"
  exec npm run dev
}

run_train() {
  echo "Training surrogate model from CSV (backend/data/Simulation_Data.csv) ..."
  cd "$ROOT"
  export PYTHONPATH="$ROOT:$PYTHONPATH"
  exec "$PYTHON" backend/scripts/train_surrogate_model.py --csv
}

run_all() {
  echo "Starting backend in background, then frontend in foreground."
  echo "Backend log: $ROOT/backend.log"
  cd "$ROOT/backend"
  export PYTHONPATH="$ROOT:$PYTHONPATH"
  "$PYTHON" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload > "$ROOT/backend.log" 2>&1 &
  BACKEND_PID=$!
  echo "Backend PID: $BACKEND_PID"
  sleep 3
  cd "$ROOT/frontend"
  npm run dev
  kill $BACKEND_PID 2>/dev/null || true
}

usage() {
  echo "Usage: $0 [backend|frontend|train|all]"
  echo ""
  echo "  backend   – Start FastAPI backend (port 8000). Run first."
  echo "  frontend  – Start Vite frontend. Run in a second terminal after backend."
  echo "  train     – Train surrogate model from backend/data/Simulation_Data.csv."
  echo "  all       – Start backend in background, then frontend (single terminal)."
  echo ""
  echo "If .venv exists (e.g. after ./scripts/install_openems_here.sh), it is used."
  echo "Optional: set OPENEMS_PYTHON_PATH in .env for openEMS Python. See docs/OPENEMS_SETUP.md."
  echo ""
  echo "Examples:"
  echo "  $0 backend    # terminal 1"
  echo "  $0 frontend   # terminal 2"
  echo "  $0 train      # one-time training"
  echo "  $0 all        # backend + frontend in one go"
}

case "${1:-}" in
  backend)  run_backend ;;
  frontend) run_frontend ;;
  train)    run_train ;;
  all)      run_all ;;
  -h|--help|help|"") usage ;;
  *) echo "Unknown option: $1"; usage; exit 1 ;;
esac
