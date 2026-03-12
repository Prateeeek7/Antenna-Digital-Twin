import React from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';

/** Dimensions in meters (same convention as PatchViewer3D reference). */
export interface Patch3DViewProps {
  length: number;
  width: number;
  height: number;
  /** Feed position in meters (absolute). */
  feedX: number;
  feedY: number;
  className?: string;
}

const PATCH_THICKNESS_M = 35e-6;
const HEIGHT_EXAGGERATION = 12;
const SUBSTRATE_HEIGHT_FACTOR = 0.5; // substrate shown at half visual height
const SCALE_M_TO_SCENE = 1000; // 1 m = 1000 units (mm)
const SUBSTRATE_MARGIN_M = 8e-3;

function SubstrateAndPatch({ length, width, height, feedX, feedY }: Patch3DViewProps) {
  const L = length * SCALE_M_TO_SCENE;
  const W = width * SCALE_M_TO_SCENE;
  const hSub = Math.max(height, 0.2e-3) * SCALE_M_TO_SCENE * HEIGHT_EXAGGERATION * SUBSTRATE_HEIGHT_FACTOR;
  const tPatch = PATCH_THICKNESS_M * SCALE_M_TO_SCENE * HEIGHT_EXAGGERATION;
  const margin = SUBSTRATE_MARGIN_M * SCALE_M_TO_SCENE;
  const subW = W + 2 * margin;
  const subD = L + 2 * margin;
  const centerX = subW / 2;
  const centerY = subD / 2;
  // Feed position: backend feed_x is along length (patch Y), feed_y along width (patch X). Place relative to patch origin.
  const feedXScene = centerX - W / 2 + (feedY * SCALE_M_TO_SCENE);
  const feedYScene = centerY - L / 2 + (feedX * SCALE_M_TO_SCENE);

  return (
    <group>
      <mesh position={[centerX, centerY, -hSub / 2]} receiveShadow>
        <boxGeometry args={[subW, subD, hSub]} />
        <meshStandardMaterial color="#ddb174" roughness={0.9} metalness={0} />
      </mesh>
      <mesh position={[centerX, centerY, tPatch / 2]} castShadow receiveShadow>
        <boxGeometry args={[W, L, tPatch]} />
        <meshStandardMaterial color="#b87333" roughness={0.35} metalness={0.8} />
      </mesh>
      <mesh position={[feedXScene, feedYScene, tPatch + 0.5]} castShadow>
        <sphereGeometry args={[Math.min(W, L) * 0.08, 16, 16]} />
        <meshStandardMaterial color="#1a1a1a" roughness={0.3} metalness={0.9} />
      </mesh>
    </group>
  );
}

export const Patch3DView: React.FC<Patch3DViewProps> = (props) => {
  const L = props.length * SCALE_M_TO_SCENE;
  const W = props.width * SCALE_M_TO_SCENE;
  const margin = SUBSTRATE_MARGIN_M * SCALE_M_TO_SCENE;
  const subW = W + 2 * margin;
  const subD = L + 2 * margin;
  const sceneSize = Math.max(subW, subD, 40);
  const centerX = subW / 2;
  const centerY = subD / 2;
  const camDist = sceneSize * 2.2;

  return (
    <div className={props.className} style={{ width: '100%', height: '100%', minHeight: 320, background: '#0E1116' }}>
      <Canvas
        camera={{
          position: [centerX, centerY, camDist],
          fov: 50,
          up: [0, 1, 0],
        }}
        gl={{ antialias: true, alpha: false }}
      >
        <ambientLight intensity={0.6} />
        <directionalLight position={[centerX, centerY, camDist]} intensity={0.9} />
        <directionalLight position={[centerX - 30, centerY + 30, 50]} intensity={0.4} />
        <SubstrateAndPatch {...props} />
        <OrbitControls
          target={[centerX, centerY, 0]}
          enableDamping
          dampingFactor={0.05}
          screenSpacePanning
          minDistance={sceneSize * 0.6}
          maxDistance={sceneSize * 4}
        />
      </Canvas>
    </div>
  );
};
