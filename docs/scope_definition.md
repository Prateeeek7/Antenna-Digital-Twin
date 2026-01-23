# Scope Definition - Frozen Parameters

**Document Version:** 1.0  
**Date:** 2025  
**Status:** FROZEN - No changes without architecture review

## Purpose

This document defines the frozen scope parameters for the Single-Band Microstrip Patch Antenna Digital Twin system. These parameters are locked to prevent architecture drift and ensure focused development.

## Frozen Scope Parameters

### Antenna Geometry
- **Type**: Rectangular microstrip patch antenna
- **Shape**: Single rectangular patch (no arrays, no multi-patch configurations)
- **Variations**: None - single geometry type only

### Frequency Band
- **Primary Band**: 2.4 GHz (2.0 - 3.0 GHz range)
- **Secondary Band**: 3.5 GHz (3.0 - 4.0 GHz range) - configurable but not mixed
- **Operation**: Single-band operation only (no dual-band or multi-band)
- **Frequency Range**: Configurable per band, but only one band active at a time

### Substrate Materials
- **Default**: FR-4
  - Relative Permittivity (εr): 4.4
  - Loss Tangent (tan δ): 0.02
  - Typical Thickness: 1.6 mm (0.0016 m)
- **Alternative**: Rogers RO4003 and RO4350 (configurable)
- **Custom Substrates**: Supported via manual parameter entry
- **Restriction**: One substrate type per antenna instance

### Feed Types
- **Default**: Inset feed (microstrip line feed)
- **Optional**: Coaxial feed (probe feed)
- **Restriction**: One feed type per antenna instance

### Operating Modes
- **Single-Band Operation**: Only one frequency band active at a time
- **No MIMO**: Single antenna element only (no arrays)
- **No Beamforming**: No phased array capabilities

## Out of Scope (Explicitly Excluded)

1. **Multi-band antennas**: Dual-band, tri-band, or broadband designs
2. **Antenna arrays**: Phased arrays, MIMO arrays, or any multi-element configurations
3. **Different antenna types**: Only rectangular microstrip patch (no circular, triangular, etc.)
4. **Active components**: No amplifiers, phase shifters, or active matching networks
5. **mmWave frequencies**: Sub-6 GHz only (no 28 GHz, 60 GHz, etc.)
6. **Multi-substrate designs**: Stacked or multi-layer substrates
7. **Reconfigurable antennas**: No tunable or switchable elements

## Rationale

This scope lock ensures:
- **Focused Development**: Deep expertise in one antenna type rather than shallow coverage of many
- **Credible Results**: Industry-grade quality for a single use case
- **Scalable Foundation**: Once proven for one antenna, scaling becomes engineering (not research)
- **Clear Validation**: Easier to validate and gain industry acceptance

## Change Process

Any changes to frozen parameters require:
1. Architecture review
2. Impact analysis on all phases
3. Updated documentation
4. Stakeholder approval

## Notes

- This scope applies to **Phase 0 through Phase 11**
- Future phases may extend scope, but only after core system is validated
- Extensions (arrays, MIMO, mmWave) are explicitly planned as future work, not current scope


