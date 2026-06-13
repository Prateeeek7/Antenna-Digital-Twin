import React from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';

export interface DipoleAntenna3DProps {
  /** Total end-to-end length (mm) — λ/2 for a half-wave dipole */
  dipoleLengthMm: number;
  /** Physical wire radius (mm); display uses at least a minimum so rods stay visible */
  wireRadiusMm: number;
  /** Feed gap at center (mm) */
  feedGapMm: number;
  /** Canvas height (px) */
  height?: number;
}

/**
 * Classic half-wave dipole schematic: two λ/4 arms, gap at center, twin feeder lines, source.
 * Scene units: 1 = 1 mm. Rod radius uses a modest minimum so arms stay visible without looking oversized.
 */
function DipoleSchematic({
  dipoleLengthMm,
  wireRadiusMm,
  feedGapMm,
}: Omit<DipoleAntenna3DProps, 'height'>) {
  const L = Math.max(dipoleLengthMm, 0.5);
  const g = Math.min(Math.max(feedGapMm, 0.05), L * 0.95);
  const arm = Math.max((L - g) / 2, 0.05);

  // Visible rod radius — half of prior schematic scale (min ~1.4 mm, ~1% of L); still readable on screen
  const rRod = Math.max(wireRadiusMm, 1.4, L * 0.01);
  const rRodCapped = Math.min(rRod, L * 0.06);

  const leftCx = -(L + g) / 4;
  const rightCx = (L + g) / 4;

  const feederLen = Math.min(Math.max(L * 0.5, 45), 140);
  const twinSep = Math.max(rRodCapped * 1.75, 4);
  const feederR = Math.max(rRodCapped * 0.38, 0.55);
  const feederCenterY = -feederLen / 2;

  return (
    <group>
      {/* Left λ/4 arm */}
      <mesh position={[leftCx, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[rRodCapped, rRodCapped, arm, 28]} />
        <meshStandardMaterial color="#d4b968" metalness={0.55} roughness={0.32} />
      </mesh>
      {/* Right λ/4 arm */}
      <mesh position={[rightCx, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[rRodCapped, rRodCapped, arm, 28]} />
        <meshStandardMaterial color="#d4b968" metalness={0.55} roughness={0.32} />
      </mesh>
      {/* Rounded-ish ends (caps read as solid rod) */}
      <mesh position={[-L / 2, 0, 0]}>
        <sphereGeometry args={[rRodCapped, 16, 16]} />
        <meshStandardMaterial color="#d4b968" metalness={0.55} roughness={0.32} />
      </mesh>
      <mesh position={[L / 2, 0, 0]}>
        <sphereGeometry args={[rRodCapped, 16, 16]} />
        <meshStandardMaterial color="#d4b968" metalness={0.55} roughness={0.32} />
      </mesh>

      {/* Twin feeder / transmission line (parallel, vertical −Y) */}
      <mesh position={[0, feederCenterY, twinSep / 2]}>
        <cylinderGeometry args={[feederR, feederR, feederLen, 14]} />
        <meshStandardMaterial color="#94a3b8" metalness={0.35} roughness={0.48} />
      </mesh>
      <mesh position={[0, feederCenterY, -twinSep / 2]}>
        <cylinderGeometry args={[feederR, feederR, feederLen, 14]} />
        <meshStandardMaterial color="#94a3b8" metalness={0.35} roughness={0.48} />
      </mesh>

      {/* Simple source symbol (lumped RF) */}
      <mesh position={[0, -feederLen - Math.max(6, feederR * 3), 0]}>
        <sphereGeometry args={[Math.max(5, feederR * 2.2), 20, 20]} />
        <meshStandardMaterial color="#64748b" metalness={0.25} roughness={0.55} />
      </mesh>
      <mesh position={[0, -feederLen - Math.max(6, feederR * 3), 0]} rotation={[0, 0, Math.PI / 4]}>
        <torusGeometry args={[Math.max(7, feederR * 2.8), 0.9, 8, 32]} />
        <meshStandardMaterial color="#94a3b8" metalness={0.4} roughness={0.45} />
      </mesh>
    </group>
  );
}

export const DipoleAntenna3D: React.FC<DipoleAntenna3DProps> = ({
  dipoleLengthMm,
  wireRadiusMm,
  feedGapMm,
  height = 440,
}) => {
  const L = Math.max(dipoleLengthMm, 1);
  const feederExtent = Math.min(Math.max(L * 0.5, 45), 140);
  const verticalSpan = L * 0.35 + feederExtent + 20;
  const dist = Math.min(480, Math.max(140, L * 2.4 + feederExtent * 0.35));
  const targetY = -feederExtent * 0.15;

  return (
    <div
      className="dipole-antenna-3d"
      style={{
        width: '100%',
        height,
        borderRadius: 8,
        overflow: 'hidden',
        background: 'linear-gradient(165deg, #0c1220 0%, #151d2e 45%, #0a0e18 100%)',
        border: '1px solid var(--color-border-divider, #2d3748)',
      }}
    >
      <Canvas
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: false }}
        camera={{
          position: [L * 0.15, L * 0.25 + verticalSpan * 0.08, dist],
          fov: 40,
          near: 0.5,
          far: 8000,
        }}
      >
        <color attach="background" args={['#0c1220']} />
        <ambientLight intensity={0.58} />
        <directionalLight position={[90, 140, 70]} intensity={1.2} />
        <directionalLight position={[-70, 50, -90]} intensity={0.4} color="#b8d0ff" />
        <DipoleSchematic
          dipoleLengthMm={dipoleLengthMm}
          wireRadiusMm={wireRadiusMm}
          feedGapMm={feedGapMm}
        />
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -verticalSpan * 0.55, 0]}>
          <planeGeometry args={[Math.max(L * 5, 260), Math.max(L * 5, 260)]} />
          <meshStandardMaterial color="#141c2e" roughness={0.96} metalness={0.04} />
        </mesh>
        <OrbitControls
          enablePan
          minDistance={Math.max(50, L * 0.9)}
          maxDistance={Math.min(900, L * 10)}
          target={[0, targetY, 0]}
        />
      </Canvas>
    </div>
  );
};
