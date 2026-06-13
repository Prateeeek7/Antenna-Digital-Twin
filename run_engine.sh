#!/usr/bin/env bash
# Antenna Digital Twin – single script for all run commands
# Usage: ./run_engine.sh [backend|frontend|train|all]
# Default (no args): all

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

# Default 8001 so this app does not fight other FastAPI services commonly bound to 8000.
# Override in .env: BACKEND_PORT=8000
: "${BACKEND_PORT:=8001}"
export BACKEND_PORT

warn_if_port_busy() {
  local port="${1:?}"
  if command -v lsof >/dev/null 2>&1; then
    local lines
    lines=$(lsof -iTCP:"$port" -sTCP:LISTEN -n -P 2>/dev/null || true)
    if [ -n "$lines" ]; then
      echo ""
      echo "WARNING: Something is already listening on port $port."
      echo "  If that is not THIS project's FastAPI app, /api/v1/health will return 404 in the UI."
      echo "  Stop the other process, or set in repo .env: BACKEND_PORT=8002"
      echo "  and in frontend/.env.local: VITE_API_URL=http://localhost:8002"
      echo ""
      echo "$lines"
      echo ""
    fi
  fi
}

run_backend() {
  warn_if_port_busy "$BACKEND_PORT"
  echo "Starting Antenna Digital Twin backend (uvicorn) on http://0.0.0.0:${BACKEND_PORT} ..."
  cd "$ROOT/backend"
  export PYTHONPATH="$ROOT:$PYTHONPATH"
  exec "$PYTHON" -m uvicorn backend.main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload
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
  warn_if_port_busy "$BACKEND_PORT"
  echo "Starting backend in background, then frontend in foreground."
  echo "Backend log: $ROOT/backend.log (port ${BACKEND_PORT})"
  cd "$ROOT/backend"
  export PYTHONPATH="$ROOT:$PYTHONPATH"
  "$PYTHON" -m uvicorn backend.main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload > "$ROOT/backend.log" 2>&1 &
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
  echo "  backend   – Start FastAPI backend (port \$BACKEND_PORT, default 8001). Run first."
  echo "  frontend  – Start Vite frontend. Run in a second terminal after backend."
  echo "  train     – Train surrogate model from backend/data/Simulation_Data.csv."
  echo "  all       – Start backend in background, then frontend (single terminal)."
  echo ""
  echo "If .venv exists (e.g. after ./scripts/install_openems_here.sh), it is used."
  echo "Optional: set OPENEMS_PYTHON_PATH in .env for openEMS Python. See docs/OPENEMS_SETUP.md."
  echo "If 8001 is taken, set BACKEND_PORT=8002 in .env and VITE_API_URL=http://localhost:8002 in frontend/.env.local."
  echo ""
  echo "Default:"
  echo "  $0            # same as: $0 all"
  echo ""
  echo "Examples:"
  echo "  $0 backend    # terminal 1"
  echo "  $0 frontend   # terminal 2"
  echo "  $0 train      # one-time training"
  echo "  $0 all        # backend + frontend in one go"
}

case "${1:-all}" in
  backend)  run_backend ;;
  frontend) run_frontend ;;
  train)    run_train ;;
  all)      run_all ;;
  -h|--help|help) usage ;;
  *) echo "Unknown option: $1"; usage; exit 1 ;;
esac
