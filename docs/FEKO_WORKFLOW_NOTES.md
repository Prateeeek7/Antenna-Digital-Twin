## FEKO Workflow & Platform Notes

This file summarizes the key decisions and workflows discussed with the AI assistant about using **Altair FEKO** with this Antenna Digital Twin project.

---

## 1. Platform Constraints (M‑Series Mac)

- You are working on an **Apple Silicon Mac (M4)**.
- **FEKO is not supported natively on macOS** and is also **not officially supported** on:
  - Windows ARM (typically used under Parallels on M‑series Macs)
  - ARM Linux
- Because of this, the realistic way to use FEKO is to run it on a **separate Windows or supported Linux machine**, not directly on the M4.

### Practical implication

- The **digital twin codebase runs on the Mac** (backend, frontend, ML, etc.).
- **FEKO runs remotely** on a Windows or Linux machine (lab PC, workstation, VM, or cloud instance) that has:
  - FEKO installed and licensed
  - Scripting or batch access (`runfeko`, Lua macros, etc.)

---

## 2. Recommended FEKO Usage Pattern

Two main usage modes were identified:

- **A. Continuous remote solver**  
  Use FEKO as the EM ground‑truth solver during development and validation:
  - Mac: choose antenna parameters, drive simulations conceptually via the `EMSolverInterface` pattern.
  - Remote FEKO machine: receives parameters, runs FEKO, exports results (S‑parameters, patterns).

- **B. Dataset generator for surrogates**  
  Use FEKO primarily to generate a **large offline dataset** (e.g., 1000 simulations). Then:
  - Train surrogate models (GP/NN) on the Mac using that FEKO dataset.
  - During day‑to‑day usage, the digital twin relies on **ML surrogates**, not direct FEKO calls.

Mode B is often simpler and matches how the current project is structured (solver‑agnostic training followed by fast surrogate inference).

---

## 3. Plan for 1000 FEKO Simulations

The idea is **not** to click 1000 times in the GUI, but to:

1. **Create a single parametric FEKO model**
   - Build a rectangular microstrip patch in CADFEKO with variables for:
     - `L` (patch length)
     - `W` (patch width)
     - `h` (substrate thickness)
     - `feed_x`, `feed_y` (feed position / inset depth)
     - `eps_r`, `loss_tan` (substrate properties)
   - Define:
     - Frequency range (e.g. 2.0–3.0 GHz or 3.0–4.0 GHz)
     - S‑parameter request (S11 vs frequency)
     - Optional far‑field request for gain/pattern
   - Save as a **template project** (.cfx / .fek) that uses these variables.

2. **Design a DoE (Design of Experiments) with ~1000 points**
   - On the Mac (Python/NumPy, etc.), generate a CSV like:
     - `design_points.csv` with columns:
       - `id, L_mm, W_mm, h_mm, feed_x_mm, feed_y_mm, eps_r, loss_tan`
   - Choose realistic ranges consistent with the project scope (2.4 GHz / 3.5 GHz, FR‑4, etc.).

3. **Automate FEKO runs on the remote machine**
   - Use either:
     - A **CADFEKO Lua macro** that:
       - Reads `design_points.csv`.
       - Sets model variables for each row.
       - Runs the solver.
       - Exports S11 and pattern data to per‑run files.
     - Or a **command‑line script with `runfeko`** that:
       - Generates per‑run `.pre` or model files with specific parameters.
       - Calls `runfeko` for each design point (sequential or parallel).
   - For each design point, export at least:
     - **S11 vs frequency** → Touchstone (`.s1p`) or CSV.
     - Optional **radiation pattern** → CSV/JSON (`theta`, `phi`, `gain_dBi`, etc.).
     - A small `metadata.json` with the original parameters and any FEKO status.

4. **Simulations duration**
   - If one FEKO run is ~30–60 s:
     - 1000 runs ≈ 8–16 hours sequential.
     - Use multi‑core / multiple jobs if possible to shorten this.

---

## 4. Using FEKO Data in This Project

Once the 1000 FEKO runs are done and exported:

1. **Transfer data to the Mac**
   - Copy the full results directory (all `.s1p` / CSV / JSON files plus metadata) onto the Mac, inside a suitable `data/` subfolder.

2. **Convert FEKO outputs to the project’s internal format**
   - Write a Python script (on the Mac) that:
     - Parses each run’s S11/far‑field data.
     - Produces:
       - Frequency arrays
       - S11 magnitude in dB
       - Gain / efficiency / pattern arrays
     - Matches the structures used in `backend/core/models/schemas.py` (e.g. `S11Data`, `RadiationPattern`).

3. **Train surrogate models on FEKO data**
   - Use or adapt the existing training pipeline (originally built around Meep/OpenEMS) so that:
     - Training samples come from FEKO instead of Meep.
     - Surrogate models (GP/NN) now approximate FEKO’s behavior.

4. **Use the digital twin without FEKO at runtime**
   - For most interactive use (web UI, optimization, calibration), the system queries the **surrogate models**, not FEKO.
   - FEKO remains a **ground‑truth tool** used occasionally for:
     - Generating more training data.
     - Validating surrogate predictions.

---

## 5. Notes About Chat History and Portability

- The chat history with the AI assistant is **not stored inside this repo by default**.
- This project includes a pointer (`docs/chat_history.md`) to a separate transcript file in the `.cursor` area on your Mac.
- When you **copy the repository to a Windows machine**, that `.cursor` transcript path may not exist there.
- This `FEKO_WORKFLOW_NOTES.md` file is meant to be a **portable summary** of the key decisions so you can:
  - Open the project on Windows.
  - Quickly understand how FEKO is intended to be used with this digital twin.
  - Continue from there with minimal re‑explaining.

