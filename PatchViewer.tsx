import type { LengthUnit } from '@/lib/units'
import { PatchViewer3D } from './PatchViewer3D'

export type PatchType = 'rectangular' | 'circular'

interface PatchViewerRectangularProps {
  type: 'rectangular'
  W: number
  L: number
  /** Substrate height in meters */
  h: number
  y0?: number | null
  /** Optional feed X offset from center in meters. */
  feedXOffsetM?: number | null
  /** Optional feed Y offset from center in meters. */
  feedYOffsetM?: number | null
  lengthUnit: LengthUnit
}

interface PatchViewerCircularProps {
  type: 'circular'
  a: number
  a_e: number
  /** Substrate height in meters */
  h: number
  /** Optional feed X offset from center in meters. */
  feedXOffsetM?: number | null
  /** Optional feed Y offset from center in meters. */
  feedYOffsetM?: number | null
  lengthUnit: LengthUnit
}

type PatchViewerProps = PatchViewerRectangularProps | PatchViewerCircularProps

export function PatchViewer(props: PatchViewerProps) {
  if (props.type === 'rectangular') {
    const { W, L, h, y0, feedXOffsetM, feedYOffsetM } = props
    return (
      <div className="patch-viewer">
        <h3 className="viewer-title">Patch on substrate (3D)</h3>
        <p className="viewer-scale">
          W = {(W * 1000).toFixed(4)} mm, L = {(L * 1000).toFixed(4)} mm · Substrate h = {(h * 1000).toFixed(3)} mm · Drag to rotate
        </p>
        <PatchViewer3D type="rectangular" W={W} L={L} h={h} y0={y0} feedXOffsetM={feedXOffsetM} feedYOffsetM={feedYOffsetM} />
      </div>
    )
  }

  const { a, a_e, h, feedXOffsetM, feedYOffsetM } = props
  return (
    <div className="patch-viewer">
      <h3 className="viewer-title">Patch on substrate (3D)</h3>
      <p className="viewer-scale">
        a = {(a * 1000).toFixed(4)} mm, a_e = {(a_e * 1000).toFixed(4)} mm · Substrate h = {(h * 1000).toFixed(3)} mm · Drag to rotate
      </p>
      <PatchViewer3D type="circular" a={a} a_e={a_e} h={h} feedXOffsetM={feedXOffsetM} feedYOffsetM={feedYOffsetM} />
    </div>
  )
}
