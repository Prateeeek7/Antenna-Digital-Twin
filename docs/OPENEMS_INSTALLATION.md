# OpenEMS Installation on macOS

## Summary

OpenEMS has been successfully installed on your macOS system. This document provides details about the installation and how to use it.

## Installation Details

### Installed Components

- **OpenEMS Core**: v0.0.36-132-g05ad999
- **CSXCAD**: v0.6.3-92-g51ea4bb
- **Installation Path**: `~/openems/`
- **Executable**: `~/openems/bin/openEMS`

### Dependencies Installed

- **Octave**: 10.3.0 (via Homebrew)
- **HDF5**: 1.14.6 (for data storage)
- **CGAL**: 6.1 (Computational Geometry Algorithms Library)
- **VTK**: 9.5.2 (Visualization Toolkit)
- **TinyXML**: 2.6.2 (built from source)
- **Boost**: 1.90.0
- **fparser**: 4.5.1

## PATH Configuration

OpenEMS has been added to your PATH in `~/.zshrc`:

```bash
export PATH="$HOME/openems/bin:$PATH"
```

To use OpenEMS in the current session, run:
```bash
export PATH="$HOME/openems/bin:$PATH"
```

Or restart your terminal.

## Verification

### Test OpenEMS Installation

```bash
openEMS --version
```

You should see version information similar to:
```
---------------------------------------------------------------------- 
| openEMS 64bit -- version v0.0.36-132-g05ad999
| (C) 2010-2025 Thorsten Liebig <thorsten.liebig@gmx.de>  GPL license
----------------------------------------------------------------------
```

### Test Python Integration

```bash
cd "/Users/pratikkumar/Desktop/Antenna Digital Twin"
PYTHONPATH=/Users/pratikkumar/Desktop/Antenna\ Digital\ Twin python3 -c "from backend.em_solver.factory import EMSolverFactory; solver = EMSolverFactory.create_solver('openems'); print(f'OpenEMS: {solver.get_solver_name()}')"
```

## Usage

### Running Real EM Simulations

Now that OpenEMS is installed, you can run real EM simulations instead of mock data:

```bash
cd "/Users/pratikkumar/Desktop/Antenna Digital Twin/backend"
PYTHONPATH=/Users/pratikkumar/Desktop/Antenna\ Digital\ Twin python3 scripts/train_surrogate_model.py --samples 100
```

**Note**: Real EM simulations will take significantly longer than mock data generation. Each simulation can take minutes to hours depending on the complexity.

### Training with Real Data

The training script will automatically use OpenEMS when available. To force real EM simulation (not mock data), ensure OpenEMS is in your PATH and run:

```bash
cd "/Users/pratikkumar/Desktop/Antenna Digital Twin/backend"
PYTHONPATH=/Users/pratikkumar/Desktop/Antenna\ Digital\ Twin python3 scripts/train_surrogate_model.py --samples 10 --no-mock
```

## How It Works

1. **Octave Scripts**: OpenEMS uses Octave/Matlab scripts to define antenna geometries and simulation parameters
2. **FDTD Solver**: OpenEMS runs Finite-Difference Time-Domain (FDTD) simulations
3. **Results**: Simulation results are saved in HDF5 format and can be parsed by the backend

## Troubleshooting

### OpenEMS Not Found

If you get "OpenEMS not found in PATH":
1. Ensure `~/openems/bin` is in your PATH
2. Run: `export PATH="$HOME/openems/bin:$PATH"`
3. Verify: `which openEMS`

### Octave Not Found

If Octave is not found:
```bash
brew install octave
```

### Simulation Failures

- Check that all dependencies are installed
- Verify Octave can run: `octave --version`
- Check simulation output logs in the results directory

## Additional Resources

- **OpenEMS Documentation**: https://docs.openems.de
- **OpenEMS GitHub**: https://github.com/thliebig/openEMS-Project
- **Octave Documentation**: https://octave.org/doc/

## Notes

- The installation was built from source to ensure compatibility with macOS
- TinyXML was built from source as it's deprecated in Homebrew
- VTK, CGAL, and HDF5 were installed via Homebrew for convenience
- The build process took approximately 30-60 minutes depending on system resources

















