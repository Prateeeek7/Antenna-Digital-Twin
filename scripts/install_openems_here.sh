#!/usr/bin/env bash
# Install openEMS Python (CSXCAD + openEMS) for this project so "Run with OpenEMS" is fast.
# Creates .venv, installs backend deps, then builds openEMS-Project with Python bindings.
# Usage: ./scripts/install_openems_here.sh [openEMS-Project directory]
#   With no argument: clones openEMS-Project into backend/vendor/openEMS-Project and builds.
#   With path: uses that directory (already cloned) and builds; Python packages go into .venv.

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="$ROOT/.venv"
OPENEMS_PREFIX="${OPENEMS_PREFIX:-$ROOT/backend/opt/openEMS}"

echo "Project root: $ROOT"
echo "Venv:        $VENV"
echo "OpenEMS prefix: $OPENEMS_PREFIX"

# 1. Create venv and install backend + build deps
if [ ! -d "$VENV" ]; then
  echo "Creating .venv ..."
  python3 -m venv "$VENV"
fi
echo "Using Python: $VENV/bin/python"
export PATH="$VENV/bin:$PATH"

echo "Installing backend requirements and build deps (numpy, h5py, matplotlib, cython) ..."
"$VENV/bin/pip" install --upgrade pip
[ -f "$ROOT/requirements.txt" ] && "$VENV/bin/pip" install -r "$ROOT/requirements.txt"
"$VENV/bin/pip" install numpy h5py matplotlib cython

# 2. Resolve openEMS-Project source (must be a path WITHOUT spaces for pip to accept file:// URLs)
case "$ROOT" in
  *" "*)
    BUILD_NO_SPACES=1
    OPENEMS_BUILD_BASE="/tmp/AntennaDigitalTwin_openEMS"
    ;;
  *)
    BUILD_NO_SPACES=0
    OPENEMS_BUILD_BASE=""
    ;;
esac

if [ -n "${1:-}" ]; then
  OPENEMS_SRC="$(cd "$1" && pwd)"
  case "$OPENEMS_SRC" in *" "*) echo "WARNING: Path contains spaces; pip may fail. Run without arguments to use a path without spaces." ;; esac
  echo "Using existing openEMS-Project: $OPENEMS_SRC"
else
  if [ "$BUILD_NO_SPACES" -eq 1 ]; then
    OPENEMS_SRC="${OPENEMS_BUILD_BASE}/openEMS-Project"
    echo "Project path contains spaces; cloning openEMS-Project to $OPENEMS_SRC (path without spaces) so pip can build."
    if [ ! -d "$OPENEMS_SRC" ]; then
      mkdir -p "$OPENEMS_BUILD_BASE"
      git clone --recursive https://github.com/thliebig/openEMS-Project.git "$OPENEMS_SRC"
    else
      (cd "$OPENEMS_SRC" && git pull --recurse-submodules || true)
    fi
  else
    OPENEMS_SRC="$ROOT/backend/vendor/openEMS-Project"
    if [ ! -d "$OPENEMS_SRC" ]; then
      echo "Cloning openEMS-Project into $OPENEMS_SRC ..."
      mkdir -p "$(dirname "$OPENEMS_SRC")"
      git clone --recursive https://github.com/thliebig/openEMS-Project.git "$OPENEMS_SRC"
    else
      echo "Using existing clone: $OPENEMS_SRC"
      (cd "$OPENEMS_SRC" && git pull --recurse-submodules || true)
    fi
  fi
fi

if [ ! -f "$OPENEMS_SRC/update_openEMS.sh" ]; then
  echo "No update_openEMS.sh found. On macOS, the script may not be provided; build manually:"
  echo "  See: https://docs.openems.de/python/install.html"
  echo "  Then add to project .env: OPENEMS_PYTHON_PATH=<path-to-site-packages-or-CSXCAD-openEMS-dir>"
  exit 1
fi

# 3. Build and install openEMS (C++ + Python) with venv's python first in PATH
echo "Building openEMS (this can take several minutes) ..."
[ "$BUILD_NO_SPACES" -eq 1 ] && echo "Using clone at $OPENEMS_SRC (no spaces) so pip install works."
cd "$OPENEMS_SRC"
export PATH="$VENV/bin:$PATH"
if ./update_openEMS.sh "$OPENEMS_PREFIX" --python; then
  echo "OpenEMS build finished. Python modules are in this project's .venv."
  echo "Start the app with: ./run_engine.sh backend   (then ./run_engine.sh frontend)"
else
  echo "Build failed. You can:"
  echo "  1) Use an existing openEMS install: add to $ROOT/.env:"
  echo "     OPENEMS_PYTHON_PATH=/path/to/dir/containing/CSXCAD/and/openEMS"
  echo "  2) Build manually from $OPENEMS_SRC and install into this venv:"
  echo "     export PATH=\"$VENV/bin:\$PATH\""
  echo "     cd $OPENEMS_SRC/CSXCAD && python setup.py install"
  echo "     cd $OPENEMS_SRC/openEMS && python setup.py install"
  exit 1
fi
