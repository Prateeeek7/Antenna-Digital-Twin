# OpenEMS Python setup for this project

"Run with OpenEMS" in the app uses the **Python** interface (CSXCAD + openEMS) so simulations run in-process and stay fast. If OpenEMS Python isn’t installed, the backend falls back to Octave/OpenEMS, which is slower.

## Option 1: Install openEMS in this project (recommended)

From the project root:

```bash
./scripts/install_openems_here.sh
```

This will:

1. Create a `.venv` in the project and install backend dependencies.
2. Clone [openEMS-Project](https://github.com/thliebig/openEMS-Project) into `backend/vendor/openEMS-Project`.
3. Build openEMS (C++ and Python) with `update_openEMS.sh … --python`, using the venv’s Python so CSXCAD and openEMS are installed into `.venv`.

After that, `./run_engine.sh backend` uses `.venv` and will find CSXCAD and openEMS. No extra env vars are needed.

If you already have openEMS-Project cloned somewhere:

```bash
./scripts/install_openems_here.sh /path/to/openEMS-Project
```

**Note:** If your project path contains **spaces** (e.g. `Antenna Digital Twin`), the install script automatically clones and builds openEMS from a path without spaces (e.g. `/tmp/AntennaDigitalTwin_openEMS`) so pip can install the Python modules. C++ and Python still install into your project and venv.

On macOS, `update_openEMS.sh` may require extra build tools. If the script fails, use Option 2 or the [manual build instructions](https://docs.openems.de/python/install.html).

## Option 2: Use an existing openEMS Python install

If you already have CSXCAD and openEMS installed (e.g. in another project’s venv or from a previous build):

1. Create a `.env` file in the **project root** (same folder as `run_engine.sh`).
2. Set the path to the directory that contains the `CSXCAD` and `openEMS` packages (e.g. that venv’s `site-packages` or the build output directory):

   ```bash
   OPENEMS_PYTHON_PATH=/path/to/venv/lib/python3.12/site-packages
   ```
   or, if they live in a single directory:

   ```bash
   OPENEMS_PYTHON_PATH=/path/to/dir/containing/CSXCAD/and/openEMS
   ```

3. Start the backend with `./run_engine.sh backend`. The script loads `.env` and adds `OPENEMS_PYTHON_PATH` to `PYTHONPATH`, so the backend can import CSXCAD and openEMS.

You do **not** need a project `.venv` for this; your system (or other) Python can be used as long as `OPENEMS_PYTHON_PATH` points to the right place.

## Verifying

With the backend running, use "Run with OpenEMS" in the app. If the Python bindings are found, the simulation runs without starting Octave. If you see an error about missing CSXCAD or openEMS, check `OPENEMS_PYTHON_PATH` or re-run `./scripts/install_openems_here.sh`.

## References

- [OpenEMS Python install](https://docs.openems.de/python/install.html)
- [Clone, build and install](https://docs.openems.de/install/clone-build-install.html)
