/**
 * Hierarchical catalog: category → type → subtype for physics calculators.
 * Each subtype maps to a panel implementation id.
 */

export interface PhysicsSubtypeDef {
  id: string;
  label: string;
  panelId: string;
  /** Markdown + optional KaTeX: `$...$` inline, `$$...$$` display */
  note?: string;
}

export interface PhysicsTypeDef {
  id: string;
  label: string;
  subtypes: PhysicsSubtypeDef[];
}

export interface PhysicsCategoryDef {
  id: string;
  label: string;
  description: string;
  types: PhysicsTypeDef[];
}

export interface PhysicsLeaf {
  categoryId: string;
  categoryLabel: string;
  typeId: string;
  typeLabel: string;
  subtypeId: string;
  subtypeLabel: string;
  panelId: string;
  note?: string;
}

export const PHYSICS_CATALOG: PhysicsCategoryDef[] = [
  {
    id: 'wire',
    label: '1. Wire antennas',
    description: 'Simple conductors — dipoles, monopoles, loops, long wires.',
    types: [
      {
        id: 'dipole',
        label: 'Dipole antenna',
        subtypes: [
          { id: 'half-wave', label: 'Half-wave dipole', panelId: 'dipole-half-wave' },
          {
            id: 'folded',
            label: 'Folded dipole',
            panelId: 'dipole-folded',
            note: 'Equal-diameter arms: $Z \\approx 4 Z_{\\mathrm{dip}}$ (~292 $\\Omega$). Tune spacing for 50/75 $\\Omega$ match.',
          },
          {
            id: 'short',
            label: 'Short dipole',
            panelId: 'dipole-short',
            note: '$\\ell \\ll \\lambda$: $R_{\\mathrm{rad}} \\approx 80\\pi^2 (\\ell/\\lambda)^2$; high capacitive reactance — needs matching network.',
          },
          {
            id: 'bowtie',
            label: 'Broadband dipole (bow-tie)',
            panelId: 'dipole-half-wave',
            note: 'Planar “fat” dipole: use lower velocity factor; same resonance order as strip dipole — verify in EM solver.',
          },
          {
            id: 'inverted-v',
            label: 'Inverted-V dipole',
            panelId: 'dipole-inverted-v',
            note: 'Sloping legs shorten effective height; total wire length $> \\lambda/2$ horizontal dipole for same $f$.',
          },
        ],
      },
      {
        id: 'monopole',
        label: 'Monopole antenna',
        subtypes: [
          { id: 'quarter', label: 'Quarter-wave monopole', panelId: 'monopole-quarter' },
          {
            id: 'gp',
            label: 'Ground plane antenna',
            panelId: 'monopole-ground-plane',
            note: 'Radials $\\approx \\lambda/4$ ($\\ge 4$) approximate infinite ground; pattern and $R_{\\mathrm{in}}$ approach textbook monopole.',
          },
          {
            id: 'ifa',
            label: 'Inverted-F antenna (IFA)',
            panelId: 'monopole-ifa',
            note: 'Shunt + series trace on PCB; first-order: wire segment $\\sim \\lambda/4$ electrical with shunt to ground.',
          },
          {
            id: 'pifa',
            label: 'Planar inverted-F (PIFA)',
            panelId: 'monopole-pifa',
            note: 'Patch + shorting pin + feed; height $h \\ll \\lambda$ — resonance set by patch $L/W$ and shorting position.',
          },
          {
            id: 'top-loaded',
            label: 'Top-loaded monopole',
            panelId: 'monopole-top-loaded',
            note: 'Top hat adds capacitance; same $f$ with shorter physical height — check $h/\\lambda$ and radiation resistance.',
          },
          {
            id: 'umbrella',
            label: 'Umbrella antenna',
            panelId: 'monopole-umbrella',
            note: 'Capacitive top loading (LF/MF); electrically short vertical with large top structure.',
          },
        ],
      },
      {
        id: 'loop',
        label: 'Loop antenna',
        subtypes: [
          { id: 'small', label: 'Small loop', panelId: 'loop-small' },
          {
            id: 'large',
            label: 'Large loop',
            panelId: 'loop-large',
            note: '$C \\sim \\lambda$: multi-mode; use full-wave or measurement for impedance and pattern.',
          },
          {
            id: 'ferrite',
            label: 'Ferrite loop',
            panelId: 'loop-ferrite',
            note: '$\\mu_{\\mathrm{eff}}$ scales effective area and noise pickup; $R_{\\mathrm{rad}}$ uses $A_{\\mathrm{eff}} = \\mu_{\\mathrm{eff}} A$ (first-order).',
          },
          {
            id: 'shielded',
            label: 'Shielded loop',
            panelId: 'loop-shielded',
            note: 'Electrostatic shield gap defines magnetic pickup; equivalent small-loop analysis with reduced E-field.',
          },
        ],
      },
      {
        id: 'longwire',
        label: 'Long wire antenna',
        subtypes: [
          {
            id: 'random',
            label: 'Random wire',
            panelId: 'long-wire',
            note: 'Non-resonant length: use tuner; pattern lobes follow $\\sin^2(\\pi L/\\lambda \\cdot \\cos\\theta)$-type behavior.',
          },
          {
            id: 'beverage',
            label: 'Beverage antenna',
            panelId: 'beverage',
            note: 'Lossy traveling wave on ground; length several $\\lambda$ for LF/MF directivity along wire.',
          },
        ],
      },
    ],
  },
  {
    id: 'aperture',
    label: '2. Aperture antennas',
    description: 'Radiation through openings — horns and slots.',
    types: [
      {
        id: 'horn',
        label: 'Horn antenna',
        subtypes: [
          {
            id: 'e-plane',
            label: 'E-plane horn',
            panelId: 'horn-aperture',
            note: 'Flare in E-plane; enter aperture $a \\times b$ matching your horn orientation.',
          },
          {
            id: 'h-plane',
            label: 'H-plane horn',
            panelId: 'horn-aperture',
            note: 'Flare in H-plane; same gain formula vs physical aperture.',
          },
          { id: 'pyramidal', label: 'Pyramidal horn', panelId: 'horn-aperture' },
          {
            id: 'conical',
            label: 'Conical horn',
            panelId: 'horn-aperture',
            note: 'Circular aperture: set $a=b=$ diameter equivalent or use $A = \\pi D^2/4$.',
          },
          {
            id: 'sectoral',
            label: 'Sectoral horn',
            panelId: 'horn-aperture',
            note: 'Flare in one plane only; aperture area drives on-axis gain estimate.',
          },
        ],
      },
      {
        id: 'slot',
        label: 'Slot antenna',
        subtypes: [
          { id: 'rect', label: 'Rectangular slot', panelId: 'slot-rectangular' },
          {
            id: 'circ',
            label: 'Circular slot',
            panelId: 'slot-circular',
            note: 'First resonance: slot mean circumference $\\sim \\lambda$ (order); full-wave for accurate $Z$.',
          },
          {
            id: 'ring',
            label: 'Ring slot',
            panelId: 'slot-ring',
            note: 'Annular resonator; **first order** $r_m \\approx a$ with circular patch $\\mathrm{TM}_{11}$ radius $a$ at $f$ (see calculator). Full-wave for $w$ and ground plane.',
          },
          {
            id: 'swg',
            label: 'Slotted waveguide',
            panelId: 'slot-waveguide',
            note: 'Standing wave in guide; slot on broad wall radiates — array factor with slot spacing.',
          },
        ],
      },
    ],
  },
  {
    id: 'reflector',
    label: '3. Reflector antennas',
    description: 'Reflecting surfaces and quasi-optical feeds.',
    types: [
      {
        id: 'parabolic',
        label: 'Parabolic reflector',
        subtypes: [
          { id: 'prime', label: 'Prime focus', panelId: 'parabolic-reflector' },
          {
            id: 'cassegrain',
            label: 'Cassegrain',
            panelId: 'parabolic-reflector',
            note: 'Secondary mirror; reduce spillover — often $\\eta$ slightly higher than prime if optimized.',
          },
          {
            id: 'gregorian',
            label: 'Gregorian',
            panelId: 'parabolic-reflector',
            note: 'Elliptic subreflector; similar aperture gain formula with feed/subreflector blockage.',
          },
          {
            id: 'offset',
            label: 'Offset reflector',
            panelId: 'parabolic-reflector',
            note: 'No feed blockage in aperture; efficiency often improved — adjust $\\eta$.',
          },
        ],
      },
      {
        id: 'corner',
        label: 'Corner reflector',
        subtypes: [
          {
            id: 'std',
            label: 'Corner reflector',
            panelId: 'corner-reflector',
            note: 'Dihedral/trihedral; aperture-limited gain toward corner axis.',
          },
        ],
      },
      {
        id: 'reflectarray',
        label: 'Reflectarray antenna',
        subtypes: [
          {
            id: 'ra',
            label: 'Reflectarray',
            panelId: 'reflectarray-info',
            note: 'Element phase on flat surface; use full-wave per cell + array synthesis — no single closed form.',
          },
        ],
      },
    ],
  },
  {
    id: 'array',
    label: '4. Array antennas',
    description: 'Multiple elements — pattern multiplication and beamforming.',
    types: [
      {
        id: 'yagi',
        label: 'Yagi-Uda antenna',
        subtypes: [
          {
            id: 'std',
            label: 'Standard Yagi',
            panelId: 'yagi-uda',
            note: 'Empirical gain vs element count; optimize spacing $0.15\\text{–}0.25\\,\\lambda$ per director.',
          },
          {
            id: 'folded-driver',
            label: 'Folded dipole Yagi',
            panelId: 'yagi-folded',
            note: 'Driver $\\sim 300\\,\\Omega$ balanced; match to boom/feed — pattern similar with adjusted element lengths.',
          },
        ],
      },
      {
        id: 'lpda',
        label: 'Log periodic Dipole Array',
        subtypes: [
          {
            id: 'lpda',
            label: 'LPDA',
            panelId: 'lpda',
            note: 'Scale $\\tau$ and spacing $\\sigma$ set active region; bandwidth $\\sim 1/\\tau$ (first-order).',
          },
        ],
      },
      {
        id: 'phased',
        label: 'Phased array',
        subtypes: [
          { id: 'passive', label: 'Passive phased array', panelId: 'phased-array' },
          {
            id: 'aesa',
            label: 'Active phased array (AESA)',
            panelId: 'phased-array',
            note: 'Per-element T/R modules; same array factor math for beam steering.',
          },
          {
            id: 'dbf',
            label: 'Digital beamforming array',
            panelId: 'phased-array',
            note: 'Weights in DSP; grating lobes set by element spacing $d/\\lambda$.',
          },
        ],
      },
      {
        id: 'collinear',
        label: 'Collinear array',
        subtypes: [
          {
            id: 'col',
            label: 'Collinear array',
            panelId: 'collinear-array',
            note: 'Stacked $\\lambda/2$ elements along axis; narrow elevation pattern, gain $\\sim N$ in ideal case.',
          },
        ],
      },
      {
        id: 'broadside',
        label: 'Broadside array',
        subtypes: [
          {
            id: 'bs',
            label: 'Broadside array',
            panelId: 'broadside-array',
            note: 'Uniform excitation, phase equal; peak normal to line of elements.',
          },
        ],
      },
      {
        id: 'endfire',
        label: 'End-fire array',
        subtypes: [
          {
            id: 'ef',
            label: 'End-fire array',
            panelId: 'endfire-array',
            note: 'Progressive phase for Hansen–Woodyard-type directivity along array axis ($\\mathrm{AF}(\\psi)$ end-fire).',
          },
        ],
      },
    ],
  },
  {
    id: 'microstrip',
    label: '5. Microstrip / printed',
    description: 'PCB resonators and printed radiators.',
    types: [
      {
        id: 'patch',
        label: 'Patch antenna',
        subtypes: [
          { id: 'rect', label: 'Rectangular patch', panelId: 'ms-patch-rectangular' },
          {
            id: 'circ',
            label: 'Circular patch',
            panelId: 'ms-patch-circular',
            note: '$\\mathrm{TM}_{11}$ dominant; radius from $1.841$ with $\\varepsilon_{\\mathrm{eff}}$ and fringing.',
          },
          {
            id: 'tri',
            label: 'Triangular patch',
            panelId: 'ms-patch-triangular',
            note: 'Equilateral first-order scale: $s \\approx c/(3f\\sqrt{\\varepsilon_{\\mathrm{eff}}})$.',
          },
          {
            id: 'annular',
            label: 'Annular ring patch',
            panelId: 'ms-patch-annular',
            note: 'Narrow ring: mean radius similar order to circular patch $\\mathrm{TM}_{11}$.',
          },
        ],
      },
      {
        id: 'printed-dipole',
        label: 'Printed dipole',
        subtypes: [
          {
            id: 'pd',
            label: 'Printed dipole',
            panelId: 'printed-dipole',
            note: 'Strip on substrate: electrical length $\\sim \\lambda_{\\mathrm{eff}}/2$ with $\\varepsilon_{\\mathrm{eff}}$ of line.',
          },
        ],
      },
      {
        id: 'printed-slot',
        label: 'Printed slot',
        subtypes: [
          {
            id: 'ps',
            label: 'Printed slot',
            panelId: 'printed-slot',
            note: 'Complementary to printed dipole (Booker); length shortened by $\\sqrt{\\varepsilon_{\\mathrm{eff}}}$.',
          },
        ],
      },
      {
        id: 'fractal',
        label: 'Fractal antenna',
        subtypes: [
          {
            id: 'fr',
            label: 'Fractal antenna',
            panelId: 'fractal-info',
            note: 'Multi-band from self-similar path; use **Fractal scaling** tool + EM simulation per iteration order.',
          },
        ],
      },
      {
        id: 'meta',
        label: 'Metamaterial antenna',
        subtypes: [
          {
            id: 'mt',
            label: 'Metamaterial / EBG',
            panelId: 'metamaterial-info',
            note: 'Sub-wavelength resonators; use **Maxwell–Garnett** + **LC** tools — narrowband; validate with Bloch/FEM.',
          },
        ],
      },
    ],
  },
  {
    id: 'travelling',
    label: '6. Travelling-wave antennas',
    description: 'Structure supports a traveling current wave.',
    types: [
      {
        id: 'helix',
        label: 'Helical antenna',
        subtypes: [
          {
            id: 'normal',
            label: 'Normal mode',
            panelId: 'helix-normal',
            note: 'Electrically small: behaves as loop + dipole mix; R_rad scaling below.',
          },
          { id: 'axial', label: 'Axial mode', panelId: 'helix-axial' },
        ],
      },
      {
        id: 'spiral',
        label: 'Spiral antenna',
        subtypes: [
          {
            id: 'arch',
            label: 'Archimedean spiral',
            panelId: 'spiral-archimedean',
            note: 'Band $\\sim f_{\\mathrm{low}} = c/(2\\pi R_{\\max})$ to $f_{\\mathrm{high}} = c/(2\\pi R_{\\min})$ (transmission-line model).',
          },
          {
            id: 'log',
            label: 'Log spiral',
            panelId: 'spiral-log',
            note: 'Self-complementary $\\approx 188\\,\\Omega$ on infinite substrate; practical finite ground changes $Z$.',
          },
        ],
      },
      {
        id: 'v',
        label: 'V antenna',
        subtypes: [
          {
            id: 'v',
            label: 'V antenna',
            panelId: 'v-antenna',
            note: 'Two legs; gain between dipole and traveling-wave rhombic leg pair.',
          },
        ],
      },
      {
        id: 'rhombic',
        label: 'Rhombic antenna',
        subtypes: [
          {
            id: 'rh',
            label: 'Rhombic',
            panelId: 'rhombic',
            note: 'Traveling wave on long legs; rough gain scales with $L/\\lambda$.',
          },
        ],
      },
    ],
  },
  {
    id: 'lens',
    label: '7. Lens antennas',
    description: 'Dielectric focusing.',
    types: [
      {
        id: 'lens',
        label: 'Lens antennas',
        subtypes: [
          {
            id: 'dielectric',
            label: 'Dielectric lens',
            panelId: 'lens-aperture',
            note: 'Aperture gain same as horn ($G \\approx 4\\pi \\eta A/\\lambda^2$); lens corrects phase — set $\\eta$ from illumination taper.',
          },
          {
            id: 'zoned',
            label: 'Zoned lens',
            panelId: 'lens-aperture',
            note: 'Stepped zones reduce thickness; bandwidth limited by zone jumps.',
          },
          {
            id: 'fresnel',
            label: 'Fresnel lens',
            panelId: 'lens-aperture',
            note: 'Zone plate / stepped surface; same order aperture area for gain estimate.',
          },
        ],
      },
    ],
  },
  {
    id: 'frequency-independent',
    label: '8. Frequency-independent',
    description: 'Self-scaling geometry (within practical limits).',
    types: [
      {
        id: 'fi-lp',
        label: 'Log periodic',
        subtypes: [
          {
            id: 'lp',
            label: 'Log periodic',
            panelId: 'fi-log-periodic',
            note: 'Active region moves with frequency; $\\tau$ defines bandwidth ratio $B \\approx 1/\\tau$.',
          },
        ],
      },
      {
        id: 'fi-spiral',
        label: 'Spiral',
        subtypes: [
          {
            id: 'sp',
            label: 'Spiral (FI class)',
            panelId: 'fi-spiral',
            note: 'Balanced wideband with absorber cavity; use spiral radii for band edges.',
          },
        ],
      },
      {
        id: 'fi-sin',
        label: 'Sinuous',
        subtypes: [
          {
            id: 'sin',
            label: 'Sinuous antenna',
            panelId: 'fi-sinuous',
            note: 'Dual-linear polarization over band; full-wave for element width and arm count.',
          },
        ],
      },
    ],
  },
  {
    id: 'special',
    label: '9. Special purpose',
    description: 'Application-specific and system-level RF.',
    types: [
      {
        id: 'whip',
        label: 'Whip antenna',
        subtypes: [
          {
            id: 'whip',
            label: 'Whip',
            panelId: 'monopole-quarter',
            note: 'Vehicle whip often $\\lambda/4$ or loaded; ground plane is vehicle body.',
          },
        ],
      },
      {
        id: 'discone',
        label: 'Discone',
        subtypes: [
          {
            id: 'dc',
            label: 'Discone',
            panelId: 'discone',
            note: 'Ultra-wideband; rough lower limit from cone height.',
          },
        ],
      },
      {
        id: 'biconical',
        label: 'Biconical',
        subtypes: [
          {
            id: 'bc',
            label: 'Biconical',
            panelId: 'biconical',
            note: 'Wideband; slant height $\\sim \\lambda/4$ sets lower frequency order.',
          },
        ],
      },
      {
        id: 'turnstile',
        label: 'Turnstile',
        subtypes: [
          {
            id: 'tt',
            label: 'Turnstile',
            panelId: 'turnstile',
            note: 'Two crossed dipoles 90° + quadrature for CP or RHCP/LHCP.',
          },
        ],
      },
      {
        id: 'vehicle',
        label: 'Vehicle-mounted',
        subtypes: [
          {
            id: 'veh',
            label: 'Vehicle-mounted',
            panelId: 'rf-link-budget',
            note: 'Use path loss + Friis for range; ground is imperfect GP.',
          },
        ],
      },
      {
        id: 'wearable',
        label: 'Wearable antennas',
        subtypes: [
          {
            id: 'wear',
            label: 'Wearable',
            panelId: 'rf-link-budget',
            note: 'Body detuning and SAR — EM simulation required; link budget for connectivity.',
          },
        ],
      },
      {
        id: 'reconfig',
        label: 'Reconfigurable',
        subtypes: [
          {
            id: 'rec',
            label: 'Reconfigurable',
            panelId: 'rf-link-budget',
            note: 'Switches / tuners change electrical length; per-state $S_{11}$ from measurement.',
          },
        ],
      },
      {
        id: 'mimo',
        label: 'MIMO antennas',
        subtypes: [
          {
            id: 'mimo',
            label: 'MIMO basics',
            panelId: 'mimo-correlation',
            note: 'Low envelope correlation $|\\rho|$ — spacing $d \\ge \\lambda/2$ rule of thumb at band edge.',
          },
        ],
      },
      {
        id: 'utilities',
        label: 'Port & link utilities',
        subtypes: [
          { id: 'z11', label: 'Z → Γ / |S11|', panelId: 'z-to-s11' },
          {
            id: 'friis',
            label: 'Free-space path loss & Friis',
            panelId: 'rf-path-friis',
            note: 'Friis with isotropic or dBi gains; line-of-sight only.',
          },
        ],
      },
    ],
  },
];

export function findDefaultLeaf(): PhysicsLeaf {
  const c = PHYSICS_CATALOG[0];
  const t = c.types[0];
  const s = t.subtypes[0];
  return {
    categoryId: c.id,
    categoryLabel: c.label,
    typeId: t.id,
    typeLabel: t.label,
    subtypeId: s.id,
    subtypeLabel: s.label,
    panelId: s.panelId,
    note: s.note,
  };
}

export function findLeaf(categoryId: string, typeId: string, subtypeId: string): PhysicsLeaf | null {
  const c = PHYSICS_CATALOG.find((x) => x.id === categoryId);
  if (!c) return null;
  const t = c.types.find((x) => x.id === typeId);
  if (!t) return null;
  const s = t.subtypes.find((x) => x.id === subtypeId);
  if (!s) return null;
  return {
    categoryId: c.id,
    categoryLabel: c.label,
    typeId: t.id,
    typeLabel: t.label,
    subtypeId: s.id,
    subtypeLabel: s.label,
    panelId: s.panelId,
    note: s.note,
  };
}
