import { useEffect, useRef } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'

const PATCH_THICKNESS_M = 35e-6 // 35 µm copper
const HEIGHT_EXAGGERATION = 12 // so thin substrate/patch are visible
const SCALE_M_TO_SCENE = 1000 // 1 m = 1000 units (mm)
const SUBSTRATE_MARGIN_M = 8e-3 // substrate extends 8 mm beyond patch on each side (like real PCB)

interface PatchViewer3DRectProps {
  type: 'rectangular'
  W: number
  L: number
  h: number
  y0?: number | null
  /** Feed X offset from center in meters. */
  feedXOffsetM?: number | null
  /** Feed Y offset from center in meters. */
  feedYOffsetM?: number | null
}

interface PatchViewer3DCircProps {
  type: 'circular'
  a: number
  a_e: number
  h: number
  feedXOffsetM?: number | null
  feedYOffsetM?: number | null
}

type PatchViewer3DProps = PatchViewer3DRectProps | PatchViewer3DCircProps

export function PatchViewer3D(props: PatchViewer3DProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const container = containerRef.current
    const tooltipEl = tooltipRef.current
    if (!container) return

    const width = container.clientWidth
    const height = Math.max(320, container.clientHeight || 320)

    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0xf8f8f6)

    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 10000)
    camera.lookAt(0, 0, 0)

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    // Shadows on very thin copper and substrate surfaces introduce artifacts,
    // so keep lighting simple without shadow mapping.
    renderer.shadowMap.enabled = false
    container.appendChild(renderer.domElement)

    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.05
    controls.screenSpacePanning = true

    const ambient = new THREE.AmbientLight(0xffffff, 0.6)
    scene.add(ambient)
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.85)
    dirLight.position.set(60, 80, 60)
    scene.add(dirLight)
    const fillLight = new THREE.DirectionalLight(0xffffff, 0.25)
    fillLight.position.set(-40, 20, -40)
    scene.add(fillLight)

    const s = SCALE_M_TO_SCENE
    const ex = HEIGHT_EXAGGERATION
    const hSub = Math.max(props.h, 0.2e-3) * s * ex
    const tPatch = PATCH_THICKNESS_M * s * ex

    const margin = SUBSTRATE_MARGIN_M * s // margin in scene units (mm)
    let sceneSize: number

    if (props.type === 'rectangular') {
      const { W, L } = props
      const w = W * s
      const d = L * s
      const subW = w + 2 * margin
      const subD = d + 2 * margin
      sceneSize = Math.max(subW, subD, 40)

      // Substrate = larger base extending beyond patch on all sides
      const substrateGeom = new THREE.BoxGeometry(subW, hSub, subD)
      const substrateMat = new THREE.MeshStandardMaterial({
        color: 0xddb174,
        roughness: 0.9,
        metalness: 0,
      })
      const substrate = new THREE.Mesh(substrateGeom, substrateMat)
      substrate.name = 'substrate'
      substrate.position.y = hSub / 2
      scene.add(substrate)

      // Patch = designed W×L on top of substrate, centered
      const patchGeom = new THREE.BoxGeometry(w, tPatch, d)
      const patchMat = new THREE.MeshStandardMaterial({
        color: 0xb87333,
        roughness: 0.35,
        metalness: 0.8,
      })
      const patch = new THREE.Mesh(patchGeom, patchMat)
      patch.name = 'patch'
      patch.position.y = hSub + tPatch / 2
      scene.add(patch)

      // Feed position marker: only when user has entered at least one feed offset value
      const hasFeed = props.feedXOffsetM != null || props.feedYOffsetM != null
      if (hasFeed) {
        const feedXM = props.feedXOffsetM ?? 0
        const feedYM = props.feedYOffsetM ?? (props.y0 != null ? props.y0 - L / 2 : 0)
        const feedSphere = new THREE.Mesh(
          new THREE.SphereGeometry(Math.min(w, d) * 0.08, 16, 16),
          new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: 0.3, metalness: 0.9 })
        )
        feedSphere.position.set(feedXM * s, hSub + tPatch, feedYM * s)
        feedSphere.name = 'feed'
        scene.add(feedSphere)
      }
    } else {
      const { a } = props
      const r = a * s
      const slabSize = 2 * r + 2 * margin
      sceneSize = Math.max(slabSize, 40)

      // Substrate = square base larger than circular patch
      const substrateGeom = new THREE.BoxGeometry(slabSize, hSub, slabSize)
      const substrateMat = new THREE.MeshStandardMaterial({
        color: 0xddb174,
        roughness: 0.9,
        metalness: 0,
      })
      const substrate = new THREE.Mesh(substrateGeom, substrateMat)
      substrate.name = 'substrate'
      substrate.position.y = hSub / 2
      scene.add(substrate)

      // Patch = circular disc on top, centered
      const patchGeom = new THREE.CylinderGeometry(r, r, tPatch, 48)
      const patchMat = new THREE.MeshStandardMaterial({
        color: 0xb87333,
        roughness: 0.35,
        metalness: 0.8,
      })
      const patch = new THREE.Mesh(patchGeom, patchMat)
      patch.name = 'patch'
      patch.position.y = hSub + tPatch / 2
      scene.add(patch)

      // Feed position marker: only when user has entered at least one feed offset value
      const hasFeed = props.feedXOffsetM != null || props.feedYOffsetM != null
      if (hasFeed) {
        const feedXM = props.feedXOffsetM ?? 0
        const feedZM = props.feedYOffsetM ?? 0
        const feedSphere = new THREE.Mesh(
          new THREE.SphereGeometry(r * 0.12, 16, 16),
          new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: 0.3, metalness: 0.9 })
        )
        feedSphere.position.set(feedXM * s, hSub + tPatch, feedZM * s)
        feedSphere.name = 'feed'
        scene.add(feedSphere)
      }
    }

    const dist = sceneSize * 1.6
    camera.position.set(dist * 0.7, dist * 0.6, dist * 0.7)
    controls.minDistance = sceneSize * 0.5
    controls.maxDistance = sceneSize * 4

    const raycaster = new THREE.Raycaster()
    const mouse = new THREE.Vector2()
    const fmt = (v: number) => (v * 1000).toFixed(3)

    const showTooltip = (text: string, clientX: number, clientY: number) => {
      if (!tooltipEl) return
      tooltipEl.textContent = text
      tooltipEl.style.display = 'block'
      tooltipEl.style.left = `${clientX + 12}px`
      tooltipEl.style.top = `${clientY + 12}px`
    }
    const hideTooltip = () => {
      if (tooltipEl) tooltipEl.style.display = 'none'
    }

    const onPointerMove = (e: PointerEvent) => {
      const rect = renderer.domElement.getBoundingClientRect()
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1
      raycaster.setFromCamera(mouse, camera)
      const hits = raycaster.intersectObjects(scene.children, true)
      if (hits.length > 0 && hits[0].object instanceof THREE.Mesh) {
        const name = hits[0].object.name
        if (name === 'substrate') {
          const hVal = props.h
          showTooltip(`Substrate (dielectric base)\nh = ${fmt(hVal)} mm — height`, e.clientX, e.clientY)
        } else if (name === 'patch') {
          if (props.type === 'rectangular') {
            const { W, L } = props
            showTooltip(`Patch (copper)\nW = ${fmt(W)} mm — width\nL = ${fmt(L)} mm — length`, e.clientX, e.clientY)
          } else {
            const { a, a_e } = props
            showTooltip(`Patch (copper)\na = ${fmt(a)} mm — radius\na_e = ${fmt(a_e)} mm — effective radius`, e.clientX, e.clientY)
          }
        } else if (name === 'feed') {
          showTooltip('Feed point position', e.clientX, e.clientY)
        } else {
          hideTooltip()
        }
      } else {
        hideTooltip()
      }
    }
    const onPointerLeave = () => hideTooltip()

    renderer.domElement.addEventListener('pointermove', onPointerMove)
    renderer.domElement.addEventListener('pointerleave', onPointerLeave)

    let frameId: number
    function animate() {
      frameId = requestAnimationFrame(animate)
      controls.update()
      renderer.render(scene, camera)
    }
    animate()

    const onResize = () => {
      if (!container) return
      const w = container.clientWidth
      const h = Math.max(320, container.clientHeight)
      camera.aspect = w / h
      camera.updateProjectionMatrix()
      renderer.setSize(w, h)
    }
    window.addEventListener('resize', onResize)

    return () => {
      renderer.domElement.removeEventListener('pointermove', onPointerMove)
      renderer.domElement.removeEventListener('pointerleave', onPointerLeave)
      window.removeEventListener('resize', onResize)
      cancelAnimationFrame(frameId)
      controls.dispose()
      renderer.dispose()
      container.removeChild(renderer.domElement)
    }
  }, [
    props.type,
    (props as PatchViewer3DRectProps).W,
    (props as PatchViewer3DRectProps).L,
    props.h,
    (props as PatchViewer3DRectProps).y0,
    (props as PatchViewer3DRectProps).feedXOffsetM,
    (props as PatchViewer3DRectProps).feedYOffsetM,
    (props as PatchViewer3DCircProps).a,
    (props as PatchViewer3DCircProps).feedXOffsetM,
    (props as PatchViewer3DCircProps).feedYOffsetM,
  ])

  return (
    <div className="patch-viewer-3d-wrapper">
      <div
        ref={containerRef}
        className="patch-viewer-3d"
        style={{ width: '100%', minHeight: '380px', height: '100%' }}
      />
      <div
        ref={tooltipRef}
        className="patch-viewer-3d-tooltip"
        aria-hidden
      />
    </div>
  )
}
