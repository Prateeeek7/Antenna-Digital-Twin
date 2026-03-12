**One script for all runs:** `./run_engine.sh [backend|frontend|train|all]` (from project root).

**Run in this order (both must be running):**

1. **Backend** (start first; leave this terminal open)
   ```bash
   ./run_engine.sh backend
   ```
   Or: `cd backend && export PYTHONPATH="..:$PYTHONPATH" && python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload`
   Wait until you see: `Application startup complete` and `Uvicorn running on http://0.0.0.0:8000`.

2. **Frontend** (in a second terminal)
   ```bash
   ./run_engine.sh frontend
   ```
   Or: `cd frontend && npm run dev`

If you see "Cannot reach backend" in the app:
- **Start the backend** (step 1) and leave that terminal open.
- If it’s already running but the app still shows the error, the backend may be **stuck**. In the terminal where the backend is running, press **Ctrl+C** to stop it, then run the backend command again. In another terminal you can check: `curl -s http://localhost:8000/health` — you should see `{"status":"healthy"}`.

**Train model (required for “Run Simulation” with surrogate)**
- “Run Simulation” uses the trained surrogate model by default. If you see **Model not found: …/default_s11_min.pkl**, train once from your CSV (e.g. `backend/data/Simulation_Data.csv`):
  ```bash
  cd "/Users/pratikkumar/Desktop/Antenna Digital Twin" && export PYTHONPATH="/Users/pratikkumar/Desktop/Antenna Digital Twin:$PYTHONPATH" && python3 backend/scripts/train_surrogate_model.py --csv
  ```
- Models are saved under `backend/models/`. Restart the backend after training if it was already running.

**Model vs OpenEMS results:** Training data (CSV) is from OpenEMS but only stores *scalars* (S11 min, gain, efficiency). The model is trained on those; the *S11 curve* shown for the model is a formula-based (RLC) shape, not the stored OpenEMS curve—so the *curve* will always look different. Compare the **numbers** (S11 min, gain, efficiency); they should be close for designs in the training range. Both paths now use the same feed position (X and Y).

**Run with OpenEMS** (in the app): Full FDTD (1–5 min). Uses openEMS Python (CSXCAD + openEMS). Gain and efficiency use the **same formulas** as the dataset generator: efficiency = Prad/P_acc at resonance, gain_dBi = 10×log10(efficiency×Dmax). For closest agreement with the model and CSV, run with **fast mode unchecked** (same 201 freq points, 30k steps, 20 cells/λ as the dataset).
  ```bash
  ./scripts/install_openems_here.sh
  ```
  Then start the backend with `./run_engine.sh backend` (it will use the new `.venv`). See **docs/OPENEMS_SETUP.md** for using an existing openEMS install via `OPENEMS_PYTHON_PATH` in a project `.env`.