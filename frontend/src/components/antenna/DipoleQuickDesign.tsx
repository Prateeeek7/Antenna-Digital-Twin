import React, { useMemo, useState } from 'react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { DipoleAntenna3D } from '../visualization/DipoleAntenna3D';
import { useAntennaStore } from '../../services/state';
import { decodeDipolePhysicalFromGeometry } from '../../utils/dipoleParams';
import './AntennaDesigner.css';
import './DipoleQuickDesign.css';

const C_MM_GHZ = 299.792458;
const DEFAULT_R_MM = 1;
const DEFAULT_GAP_MM = 1;

/**
 * λ/2 length from the frequency field drives the 3D total length. Wire radius & gap come from Designer when set.
 */
export const DipoleQuickDesign: React.FC = () => {
  const { parameters } = useAntennaStore();
  const [fGHz, setFGHz] = useState(2.4);
  const lengthMm = useMemo(() => C_MM_GHZ / (2 * Math.max(fGHz, 0.01)), [fGHz]);

  const fromDesigner = useMemo(() => {
    if (!parameters?.geometry) return null;
    return decodeDipolePhysicalFromGeometry(parameters.geometry);
  }, [parameters]);

  /** Total length in 3D follows this tab’s λ/2 estimate (GHz input). */
  const dipoleLengthMm = lengthMm;
  const wireRadiusMm = fromDesigner?.wireRadiusMm ?? DEFAULT_R_MM;
  const feedGapMm = fromDesigner?.feedGapMm ?? DEFAULT_GAP_MM;

  return (
    <div className="antenna-designer dipole-quick-design">
      <div className="section-header">Dipole quick estimate & 3D preview</div>
      <p className="result-comparison-note" style={{ marginBottom: 12, maxWidth: 720 }}>
        Changing <strong>Target frequency</strong> updates the λ/2 length and the <strong>3D preview</strong> immediately.
        Wire radius and feed gap use the <strong>Designer</strong> tab when available, otherwise 1 mm defaults.
      </p>

      <div className="dipole-quick-design-grid">
        <div className="antenna-designer-form" style={{ maxWidth: 520 }}>
          <div className="input-group">
            <Input
              label="Target frequency (λ/2 estimate)"
              type="number"
              unit="GHz"
              value={fGHz.toString()}
              onChange={(e) => setFGHz(parseFloat(e.target.value) || 0)}
              min="0.1"
              max="20"
              step="0.01"
            />
          </div>
          <p style={{ marginTop: 12, fontSize: 13 }}>
            Approx. half-wave length: <strong className="mono">{lengthMm.toFixed(2)} mm</strong>
          </p>
          <div className="dipole-quick-design-dims">
            3D — L (λ/2 from f): {dipoleLengthMm.toFixed(2)} mm · R: {wireRadiusMm.toFixed(3)} mm · gap: {feedGapMm.toFixed(3)}{' '}
            mm
            {fromDesigner ? ' (R & gap from Designer)' : ' (R & gap defaulted)'}
          </div>
          <p className="result-comparison-note" style={{ marginTop: 16 }}>
            Use the <strong>Designer</strong> tab to set exact dipole inputs and run the surrogate.
          </p>
          <Button variant="secondary" onClick={() => setFGHz(2.4)}>
            Reset 2.4 GHz
          </Button>
        </div>

        <div>
          <DipoleAntenna3D
            dipoleLengthMm={dipoleLengthMm}
            wireRadiusMm={wireRadiusMm}
            feedGapMm={feedGapMm}
            height={400}
          />
          <p className="dipole-quick-design-3d-caption">
            Schematic-style view: two λ/4 arms, center gap, twin feeder lines, and source. Length follows <strong>Target frequency</strong>{' '}
            (λ/2). Orbit: drag to rotate, scroll to zoom.
          </p>
        </div>
      </div>
    </div>
  );
};
