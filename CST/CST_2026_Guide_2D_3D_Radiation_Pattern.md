# CST Studio Suite 2026 Student – Parametric Microstrip Patch: 2D & 3D Radiation Pattern Simulation and Export

This guide walks through every step to build a **parametric rectangular microstrip patch antenna** in CST Studio Suite 2026 Student Edition, run simulations for **S11, 2D and 3D radiation patterns**, and **export results** in available formats.

---

## Table of Contents

1. [Part 1: Launch and Project Setup](#part-1-launch-and-project-setup)
2. [Part 2: Define Global Parameters (Parametric Design)](#part-2-define-global-parameters-parametric-design)
3. [Part 3: Create Geometry (Parametric 3D Model)](#part-3-create-geometry-parametric-3d-model)
4. [Part 4: Define Excitation (Port)](#part-4-define-excitation-port)
5. [Part 5: Boundary Conditions and Background](#part-5-boundary-conditions-and-background)
6. [Part 6: Frequency and Solver Settings](#part-6-frequency-and-solver-settings)
7. [Part 7: Define Monitors for 2D and 3D Radiation Patterns](#part-7-define-monitors-for-2d-and-3d-radiation-patterns)
8. [Part 8: Run the Simulation](#part-8-run-the-simulation)
9. [Part 9: View and Export Results](#part-9-view-and-export-results-cst-2026-student--available-formats)
10. [Part 10: Where to Put the CSV and How to Run Simulations From It](#part-10-where-to-put-the-csv-and-how-to-run-simulations-from-it)
11. [Part 11: Parameter Ranges (Quick Reference)](#part-11-parameter-ranges-quick-reference)

---

## Part 1: Launch and Project Setup

### 1.1 Start CST

1. Launch **CST Studio Suite 2026** (Student Version).
2. Wait for the main window to open.

### 1.2 Create a New Project

1. Go to **File → New**.
2. In the **New Project** dialog, select **Microwave & RF / Optical** (or **CST Microwave Studio**).
3. Click **Next**.
4. Choose **Antenna (Planar)** or **Empty Project** (we will build from scratch).
5. Click **Finish**.
6. Save the project: **File → Save As** → choose a folder and name (e.g. `MicrostripPatch_2p4GHz.cst`).

### 1.3 Set Units

1. In the menu bar: **Modeling → Units** (or **Edit → Preferences → Units**).
2. Set:
   - **Length**: `mm`
   - **Frequency**: `GHz`
   - **Time**: `ns`
3. Click **OK**.

### 1.4 Coordinate System (Reference)

- **X**: patch width direction.
- **Y**: patch length direction.
- **Z**: substrate height (normal to patch).
- Origin at centre of patch in XY; substrate from Z = 0 to Z = h.

---

## Part 2: Define Global Parameters (Parametric Design)

### 2.1 Open the Parameters List

1. In the **Navigation Tree** (left), expand **Model** if needed.
2. Right‑click **Parameters** (or go to **Modeling → Parameters**).
3. Select **Parameter List** (or **Edit Parameters**).

### 2.2 Add Geometry Parameters (in mm)

Add each parameter one by one. For each:

- **Name**: exact spelling as below (case-sensitive in formulas).
- **Value**: default (number).
- **Unit**: `mm` for lengths.

| Name   | Default | Description        | Typical range (training) |
|--------|---------|--------------------|---------------------------|
| `L`    | 32.5    | Patch length       | 30 – 35 mm                |
| `W`    | 28.5    | Patch width        | 26 – 31 mm                |
| `h`    | 1.6     | Substrate height   | 1.2 – 2.0 mm              |

Steps to add one parameter (e.g. `L`):

1. In Parameter List, click **New** or **Add**.
2. **Name**: type `L` (no spaces).
3. **Expression/Value**: type `32.5` (or select "Constant" and enter 32.5).
4. **Unit**: choose `mm` from the unit dropdown.
5. Click **OK** or **Apply**. Repeat for `W`, then `h`.

### 2.3 Substrate Margin and Substrate Size

1. Add parameter **`sub_margin`** = `10` (unit: mm). Extra margin around patch for substrate/ground.
2. Add **`L_sub`** = `L + 2*sub_margin` (expression).
3. Add **`W_sub`** = `W + 2*sub_margin` (expression).

### 2.4 Feed Position Parameters

1. Add **`feed_offset_mm`** = `-5` (unit: mm). Offset from patch centre along length (Y); training range about −7 to −3 mm.
2. Add **`feed_y_mm`** = `L/2 + feed_offset_mm` (expression, unit: mm). Absolute Y position of feed from origin.
3. Add **`feed_x_mm`** = `0` (unit: mm). Feed at centre in width (X).

(If your CSV uses metres, you can add parameters in m and use them in formulas, or convert in the macro when driving from CSV.)

### 2.5 Material Parameters

1. Add **`eps_r`** = `4.4` (no unit). Relative permittivity.
2. Add **`tan_delta`** = `0.02` (no unit). Loss tangent.

### 2.6 Frequency Parameters

1. Add **`f0`** = `2.45` (unit: GHz). Design / resonance frequency.
2. Add **`fmin`** = `2.0` (unit: GHz).
3. Add **`fmax`** = `3.0` (unit: GHz).

Click **OK** to close the Parameter List.

---

## Part 3: Create Geometry (Parametric 3D Model)

### 3.1 Substrate (Dielectric Brick)

1. In the menu bar, click **Modeling**.
2. Go to **Shapes → Brick** (or find **Brick** in the modeling toolbar and click it).
3. In the Brick dialog:
   - **Name**: `Substrate`.
   - **X min**: type `-W_sub/2` (or use the formula button and enter the expression).
   - **X max**: `W_sub/2`
   - **Y min**: `-L_sub/2`
   - **Y max**: `L_sub/2`
   - **Z min**: `0`
   - **Z max**: `h`
   - Ensure **Unit** is mm.
3. **Material**: leave **Vacuum** or **Default** for now (we will assign a custom material later).
4. Click **OK**. You should see a brick centred in XY.

### 3.2 Ground Plane (Bottom Conductor)

1. **Modeling → Shapes → Rectangle** (or **Sheet → Rectangle**).
2. **Name**: `Ground`.
3. **Plane**: choose **Z = 0** (XY plane at bottom of substrate).
4. **Corner 1**: X = `-W_sub/2`, Y = `-L_sub/2`.
5. **Corner 2**: X = `W_sub/2`, Y = `L_sub/2`.
6. **Material**: **PEC** (Perfect Electric Conductor). If PEC is not in the list, create a new material with conductivity very high (e.g. 1e10) or choose **Copper**.
7. Click **OK**.

### 3.3 Patch (Top Conductor)

1. **Modeling → Shapes → Rectangle** (or **Sheet → Rectangle**).
2. **Name**: `Patch`.
3. **Plane**: **Z = h** (top of substrate).
4. **Corner 1**: X = `-W/2`, Y = `-L/2`.
5. **Corner 2**: X = `W/2`, Y = `L/2`.
6. **Material**: **PEC** (or Copper).
7. Click **OK**.

### 3.4 Feed (Discrete Port – Probe)

We model the feed as a small conductive cylinder (probe) and excite it with a discrete port.

1. **Modeling → Shapes → Cylinder**.
2. **Name**: `FeedPin`.
3. **Axis**: **Z** (cylinder along Z).
4. **Center**: X = `feed_x_mm`, Y = `feed_y_mm`, Z = `0` (or slightly below 0 if you want via through ground).
5. **Radius**: `0.5` (mm). Inner radius if you need a tube; for solid pin use this as outer radius.
6. **Z min**: `0`.
7. **Z max**: `h` (touches patch).
8. **Material**: **PEC** or **Copper**.
9. Click **OK**.

### 3.5 Assign Material to Substrate

1. **Modeling → Materials → New Material** (or open Material Library).
2. **Name**: `Substrate_FR4`.
3. **Type**: **Normal** (dielectric).
4. **Epsilon**: set to **Parameter**: `eps_r` (or type the parameter name so it links).
5. **Mue**: `1`.
6. **Tan Delta (Dielectric)**: set to parameter `tan_delta`.
7. Save/OK.
8. In the **Navigation Tree**, select the **Substrate** brick → right‑click **Properties** (or double‑click) → **Material** → choose **Substrate_FR4** → OK.

---

## Part 4: Define Excitation (Port)

### 4.1 Define Discrete Port at Feed

1. In the **Navigation Tree**, go to **Simulation → Excitation List** (or **Waveguide Ports / Discrete Ports** depending on CST version).
2. **Excitation → Discrete Port** (or **Simulation → Discrete Port**).
3. **Pick** the two faces: one on the bottom of the feed pin (at Z = 0) and one on the top (at Z = h), or pick the feed pin and let CST suggest the port. Alternatively, use **Discrete Port** between ground and patch at the feed location.
4. In the Discrete Port dialog:
   - **Name**: `Port1`.
   - **Resistance**: `50` Ohm.
   - **Position**: ensure it is at the feed location (feed_x_mm, feed_y_mm).
5. Click **OK**. You should see **Port1** in the excitation list.

---

## Part 5: Boundary Conditions and Background

### 5.1 Open Boundary Conditions

1. **Simulation → Boundaries** (or **Edit → Simulation Properties → Boundaries**).

### 5.2 Set Boundaries for Radiation

1. For **X min, X max, Y min, Y max, Z min, Z max**:
   - Set to **Open (add space)** or **Open** so the antenna radiates into free space.
2. If there is an **“Add space”** or **“Distance to boundary”** option, use about **50–80 mm** (roughly 0.4–0.6 λ at 2.4 GHz) so the far field is accurate.
3. Click **OK**.

### 5.3 Background Material

1. **Modeling → Background** (or **Simulation → Background**).
2. Set **Background material** to **Vacuum** or **Normal** with epsilon = 1, mu = 1.
3. OK.

---

## Part 6: Frequency and Solver Settings

### 6.1 Set Frequency Range

1. **Simulation → Frequency** (or **Solver → Frequency**).
2. **fmin**: `fmin` (or 2.0) GHz.
3. **fmax**: `fmax` (or 3.0) GHz.
4. Use **Broadband** or **Single** as needed; for S11 and far field, broadband 2–3 GHz is typical.
5. OK.

### 6.2 Choose Solver

1. **Simulation → Solver** (or **Solve**).
2. Select **Time Domain Solver** (Transient) – standard for this type of antenna in CST.
3. Leave defaults or set **Accuracy** to **-40 dB** for S11 if available.
4. **Mesh**: **Simulation → Mesh** – ensure **Auto mesh** is on; you can refine **Lines per wavelength** (e.g. 10–20) for better accuracy. Apply.

### 6.3 Start a Test Run

1. **Simulation → Start** (or click **Start** in the solver toolbar).
2. Wait until the run finishes. Check **1D Results → S-Parameters** for S1,1 and resonance near 2.4 GHz.

---

## Part 7: Define Monitors for 2D and 3D Radiation Patterns

### 7.1 Farfield Monitor (3D Radiation Pattern)

1. **Simulation → Field Monitors** (or **Edit → Field Monitors**).
2. Click **New** or **Add**.
3. **Monitor type**: **Farfield** (Far Field).
4. **Name**: e.g. `Farfield_f0`.
5. **Frequency**: enter **`f0`** (parameter) or **2.45** GHz so the monitor is at design frequency.
6. **Theta**: **0** to **180** (deg). **Phi**: **0** to **360** (deg). Step: e.g. **5** deg for theta and phi (finer if needed: 2–3 deg).
7. Enable **Calculate farfield** (or equivalent). OK.

### 7.2 E-Plane and H-Plane (2D Cuts)

In CST, 2D radiation patterns are usually obtained from the **same Farfield monitor** by plotting cuts:

- **E-plane**: fixed phi (e.g. phi = 0° or 90°), theta from 0° to 180°.
- **H-plane**: fixed theta = 90°, phi from 0° to 360°.

No separate monitor is required; you will **plot** these from the 3D farfield result. Optionally you can add:

- **Farfield Monitor** with **E-plane** only: theta 0–180°, single phi.
- **Farfield Monitor** with **H-plane** only: phi 0–360°, theta = 90°.

For simplicity, one **3D Farfield monitor** is enough; 2D cuts are derived at post-processing/export.

---

## Part 8: Run the Simulation

1. **Simulation → Start** (or **Solve → Start**).
2. Wait until the progress bar reaches 100% and the message indicates completion.
3. Check the **Message Window** for errors. If successful, **1D Results** and **Farfield** results will be available.

---

## Part 9: View and Export Results (CST 2026 Student – Available Formats)

### 9.1 S-Parameters (S11)

1. In **Navigation Tree**: **1D Results → S-Parameters → S1,1** (or S(1,1)).
2. Double‑click to open the plot. Check resonance near 2.4 GHz.
3. **Export**:
   - Right‑click the plot or go to **Results → Export** (or **File → Export** from the plot window).
   - Choose **ASCII** or **Touchstone** (.s1p) if available in Student version.
   - **ASCII**: typically gives two columns (frequency, magnitude or real/imag). Save as `.txt` or `.csv`.
   - Select destination folder and filename (e.g. `S11_f0.txt`). Save.

### 9.2 3D Farfield (Radiation Pattern)

1. In **Navigation Tree**: **2D/3D Results → Farfield** (or **Farfields → Farfield_f0**).
2. Double‑click to open the 3D radiation pattern plot.
3. **Export 3D Farfield**:
   - In the Farfield plot window, use **Results → Export** or **File → Export** (or right‑click plot).
   - In CST 2026 Student, common options:
     - **Farfield (ASCII)** or **Export Farfield Data**: exports theta, phi, and gain (and optionally Etheta, Ephi) in a text file. Choose **.txt** or **.csv**.
     - **Export Plot**: saves the current view as image (**.png**, **.bmp**, **.jpg**).
   - Select **ASCII** or **CSV** for data. Set filename (e.g. `Farfield_3D_f0.txt`). Save.

### 9.3 2D Cuts (E-Plane and H-Plane)

1. Still in **Farfield** results: open the **Farfield** plot.
2. In the plot toolbar or **Plot → Plot Properties** (or **Farfield Plot Options**):
   - Choose **Polar** or **Cartesian**.
   - **E-plane**: set **Phi** = 0° (or 90°, depending on your coordinate convention). The plot shows Gain vs Theta. **Export** this plot: **File → Export** → **Image** (e.g. PNG) and/or **Export Data** (ASCII) if the option is there.
   - **H-plane**: set **Theta** = 90°. The plot shows Gain vs Phi. Export similarly.
3. If **Export Data** is available for the 2D cut, save as `Eplane_f0.txt` and `Hplane_f0.txt` (theta or phi, gain columns).

### 9.4 Summary of Export Options in CST 2026 Student

| Result       | Format to use in Student version      | Typical file        |
|-------------|----------------------------------------|---------------------|
| S11         | ASCII / CSV / Touchstone (.s1p)        | S11.txt, S11.s1p    |
| 3D Farfield | Farfield ASCII / CSV (theta, phi, gain)| Farfield_3D.txt     |
| 2D E-plane  | ASCII (theta, gain) or image            | Eplane.txt, .png    |
| 2D H-plane  | ASCII (phi, gain) or image             | Hplane.txt, .png    |
| Plot image  | PNG, BMP, JPG                          | *.png etc.          |

If a specific format (e.g. Touchstone) is disabled in Student version, use **ASCII** or **CSV** for all numeric data.

**Step-by-step export (3D Farfield):**

1. In the Navigation Tree, expand **2D/3D Results** (or **Farfield**).
2. Right-click **Farfield_f0** (or the name you gave) → **Export** (or **Export Farfield**).
3. In the export dialog: choose **ASCII**, **CSV**, or **Text file**.
4. Select columns to export (e.g. Theta, Phi, Abs(Gain) or dB(Gain)).
5. Browse to the folder where you want the file (e.g. project folder or `CST/exports`).
6. Enter filename (e.g. `Farfield_3D_2p45GHz.txt`) → **Save**.

---

## Part 10: Where to Put the CSV and How to Run Simulations From It

CST does **not** have an “Upload CSV” button in the GUI. You **place the CSV file on disk** and then run a **macro** that reads that file and runs one simulation per row. Below is where to put the file and how to run the process.

### 10.1 Where to Put the CSV File

1. **Locate your CST project folder**
   - This is the folder where you saved your `.cst` file (e.g. `MicrostripPatch_2p4GHz.cst`).
   - Example: `C:\Users\YourName\Documents\CST_Projects\` or the project root of your Antenna Digital Twin repo.

2. **Copy the CSV file into that project folder (recommended)**
   - From your Antenna Digital Twin project, the CSV files are in the **`CST`** folder:
     - `CST/cst_designs_2p4GHz_10.csv`  (10 designs)
     - `CST/cst_designs_2p4GHz_100.csv`  (100 designs)
     - `CST/cst_designs_2p4GHz_500.csv`  (500 designs)
   - **Copy** the file you want to use (e.g. `cst_designs_2p4GHz_10.csv`) into the **same folder** as your `.cst` file.
   - Example: if your project is `D:\CST_Projects\MicrostripPatch_2p4GHz.cst`, put the CSV there:
     - `D:\CST_Projects\cst_designs_2p4GHz_10.csv`

3. **Why this location**
   - The macro will open the CSV using a **full path** or a **path relative to the project**. Putting the CSV next to the `.cst` file keeps the path simple and avoids “file not found” errors.

4. **Optional: use a subfolder**
   - You can instead create a subfolder, e.g. `D:\CST_Projects\csv_input\`, put the CSV there, and in the macro use that path (e.g. `csv_input\cst_designs_2p4GHz_10.csv`). Just ensure the path in the macro matches where you saved the file.

### 10.2 “Uploading” the CSV – There Is No Upload Button

- CST does **not** have a menu like “File → Import CSV” or “Upload CSV” to run batch simulations.
- You **do not upload** the CSV into CST; you **reference it by file path** in a **VBA macro**. The macro opens the file, reads each row, sets parameters, runs the solver, and (optionally) exports results.

So “upload” = **copy the CSV to the project folder** (or a known path), then **run a macro** that uses that path.

### 10.3 How to Run Simulations From the CSV (Step-by-Step)

1. **Place the CSV**  
   Copy the chosen CSV (e.g. `cst_designs_2p4GHz_10.csv`) into your CST project folder as in **10.1**.

2. **Open the Macro Editor**  
   - In the menu bar: **Macros → Macro Editor** (or **Tools → Macro → Edit**).  
   - A VBA editor window opens.

3. **Create a new macro or open an existing one**  
   - **Macros → New Macro** (or insert a new module).  
   - You will write (or paste) a script that:
     - Sets a variable with the **full path** to your CSV, e.g.  
       `csvPath = "D:\CST_Projects\cst_designs_2p4GHz_10.csv"`  
       (replace with your actual path and filename).
     - Opens the file, skips the header line, then for each data row:
       - Reads `id, L, W, h, feed_x, feed_y, eps_r, tan_delta, f0_Hz`.
       - Converts L, W, h, feed_x, feed_y from metres to mm (× 1000).
       - Calls CST to set parameters (e.g. `StoreParameter "L", L_mm`, etc.).
       - Rebuilds the model, runs the solver, then (if you added export steps) exports S11 and Farfield to files named by `id`.

4. **Set the CSV path in the macro**  
   - In the macro code, set the path variable to the **exact** location where you put the CSV (see 10.1).  
   - Example:  
     `csvPath = ProjectPath() & "\cst_designs_2p4GHz_10.csv"`  
     if your project path is the folder containing the CSV.

5. **Save the macro**  
   - In the Macro Editor: **File → Save** (or save the module). Close the editor or leave it open.

6. **Run the macro**  
   - Back in the main CST window: **Macros → Run Macro** (or **Macros → [name of your macro]**).  
   - Select the macro you wrote and click **Run**.  
   - CST will then read the CSV and run one simulation per row. Progress appears in the message window.

7. **Where the simulations run**  
   - Each run uses the **current project** (your parametric microstrip model). The macro only changes **parameters** and re-runs the **same** simulation task (S11 + Farfield). Results are stored in the project’s result tree; if you added export steps in the macro, files (e.g. `S11_id282.txt`) are written to the path you specified in the macro (e.g. project folder or an `exports` subfolder).

### 10.4 CSV Format and Parameter Conversion

Your CSV has columns: `id, L, W, h, feed_x, feed_y, eps_r, tan_delta, f0_Hz`.

- **CSV values are in metres** for L, W, h, feed_x, feed_y. CST parameters are in **mm**. In the macro, convert:  
  `L_mm = L_from_CSV * 1000`, and similarly for W, h, feed_x, feed_y.
- **eps_r**, **tan_delta**: use as-is.  
- **f0_Hz**: convert to GHz for CST (e.g. `f0 = f0_Hz / 1e9`) if you set a frequency parameter.

CST parameter names must match what you used in the model (e.g. `L`, `W`, `h`, `feed_x_mm`, `feed_y_mm`, `eps_r`, `tan_delta`, `f0`).

### 10.5 Summary: Where to “Upload” the CSV and How to Get Simulations

| Step | What to do |
|------|------------|
| **Where to put the CSV** | Copy the CSV file (e.g. `cst_designs_2p4GHz_10.csv`) into the **same folder as your .cst project file** (or a subfolder you will use in the macro path). |
| **How to “upload” it** | There is no upload. The macro **opens the CSV by path** when you run the macro. |
| **How to run simulations** | **Macros → Macro Editor**: write a macro that reads the CSV path, loops over rows, sets parameters (with m→mm conversion), then **Rebuild** and **Run** solver. **Macros → Run Macro**: run that macro to execute all rows. |
| **Where results go** | In the project’s result tree (1D/2D/3D). If your macro exports to file, results are saved to the folder path you set in the macro (e.g. project folder or `exports`). |

Exact VBA syntax (e.g. `StoreParameter`, `Rebuild`, `Solver.Run`) depends on CST 2026’s object model; the workflow above is the one to follow. If you need a ready-made VBA example for opening the CSV and setting parameters, you can add it in a separate “Macro example” subsection.

---

## Part 11: Parameter Ranges (Quick Reference)

Keep designs within these ranges for stable and meaningful results:

| Parameter        | Min   | Max   | Unit |
|------------------|-------|-------|------|
| L                | 30    | 35    | mm   |
| W                | 26    | 31    | mm   |
| h                | 1.2   | 2.0   | mm   |
| feed_offset_mm   | -7    | -3    | mm   |
| eps_r            | 3.8   | 4.6   | -    |
| tan_delta        | 0     | 0.02  | -    |
| f0               | 2.3   | 2.5   | GHz  |

---

## Checklist Summary

- [ ] New project, units mm / GHz.
- [ ] Parameters: L, W, h, sub_margin, L_sub, W_sub, feed_offset_mm, feed_y_mm, feed_x_mm, eps_r, tan_delta, f0, fmin, fmax.
- [ ] Substrate brick (parametric), material Substrate_FR4(eps_r, tan_delta).
- [ ] Ground plane (PEC) at Z = 0.
- [ ] Patch (PEC) at Z = h.
- [ ] Feed pin + Discrete Port at (feed_x_mm, feed_y_mm).
- [ ] Boundaries: Open (add space).
- [ ] Frequency 2–3 GHz, Time Domain Solver, run once.
- [ ] Farfield monitor at f0 (3D: theta 0–180°, phi 0–360°).
- [ ] Run simulation.
- [ ] Export S11 (ASCII/CSV/Touchstone), 3D Farfield (ASCII/CSV), 2D E/H-plane (data or image) in available formats in CST 2026 Student.

This gives you a full path from **parametric microstrip patch** to **2D and 3D radiation pattern** simulation and **download/export** in the formats available in CST 2026 Student Edition.
