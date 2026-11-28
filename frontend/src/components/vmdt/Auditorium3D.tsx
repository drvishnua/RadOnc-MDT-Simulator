import React, { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import * as THREE from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, Pause, Play, RotateCcw, Sparkles, X } from "lucide-react";
import DoctorAvatar from "./DoctorAvatar.js";
import {
  buildRealisticClinicianMesh,
  createContactShadowTexture,
  createFlutedWallTexture,
  createSpotAlphaTexture,
  createStageFloorTexture,
  createSurfaceBumpTexture,
} from "./auditorium3dBuilders.js";
import { TEAM_DEFINITIONS } from "../../utils/vmdtRoster.js";
import {
  DEFAULT_TEAMS,
  type AgentSeatStatus,
  type CameraPanMode,
  type TeamId,
  type VmdtAgentConfig,
} from "../../virtualMdtTypes.js";

export interface Auditorium3DProps {
  mode: "hall" | "live";
  agents: VmdtAgentConfig[];
  cameraPanMode?: CameraPanMode;
  seatStatuses?: Record<string, AgentSeatStatus>;
  seatConclusions?: Record<string, string>;
  activeSpeakerId?: string | null;
  selectedAgentId?: string | null;
  onSelectAgent?: (agentId: string | null) => void;
  onRunFirst?: (agentId: string) => void;
  onRetryAgent?: (agentId: string) => void;
  onPauseAgent?: (agentId: string) => void;
  isSimulationRunning?: boolean;
}

interface SeatPlacement {
  agent: VmdtAgentConfig;
  worldPos: THREE.Vector3;
  tierIndex: number;
}

interface WedgePlacement {
  teamId: TeamId;
  label: string;
  a0: number;
  a1: number;
  aMid: number;
  labelWorldPos: THREE.Vector3;
}

interface ScreenPoint {
  x: number;
  y: number;
}

const STATUS_HEX: Record<AgentSeatStatus, number> = {
  idle: 0x38bdf8,
  queued: 0xf59e0b,
  running: 0x3b82f6,
  completed: 0x10b981,
  failed: 0xef4444,
  paused: 0x94a3b8,
};

const STATUS_LABEL: Record<AgentSeatStatus, string> = {
  idle: "ready",
  queued: "queued",
  running: "active speaker",
  completed: "completed",
  failed: "failed",
  paused: "paused",
};

const ARC_CENTER_Z = -4.6;
const MIN_ANGLE_DEG = -72;
const MAX_ANGLE_DEG = 72;

function degToRad(deg: number): number {
  return (deg * Math.PI) / 180;
}

function polarToWorld(angleDeg: number, radius: number, y: number): THREE.Vector3 {
  const rad = degToRad(angleDeg);
  return new THREE.Vector3(
    Math.sin(rad) * radius,
    y,
    ARC_CENTER_Z + Math.cos(rad) * radius
  );
}

function buildTierSectorGeometry(
  rInner: number,
  rOuter: number,
  a0Deg: number,
  a1Deg: number,
  height: number,
  segments = 24
): THREE.BufferGeometry {
  const shape = new THREE.Shape();
  const a0 = degToRad(a0Deg);
  const a1 = degToRad(a1Deg);

  // Shape is in XY, we extrude along +Z then rotate X by -PI/2 so XY -> X, -Z
  // Using polar angle from +Y axis: x = sin(a)*r, y = -cos(a)*r so after rotateX(-PI/2) z = +cos(a)*r
  for (let i = 0; i <= segments; i += 1) {
    const t = i / segments;
    const a = a0 + t * (a1 - a0);
    const x = Math.sin(a) * rInner;
    const y = -Math.cos(a) * rInner;
    if (i === 0) shape.moveTo(x, y);
    else shape.lineTo(x, y);
  }
  for (let i = segments; i >= 0; i -= 1) {
    const t = i / segments;
    const a = a0 + t * (a1 - a0);
    const x = Math.sin(a) * rOuter;
    const y = -Math.cos(a) * rOuter;
    shape.lineTo(x, y);
  }
  shape.closePath();

  const geom = new THREE.ExtrudeGeometry(shape, {
    depth: height,
    bevelEnabled: false,
    curveSegments: segments,
  });
  geom.rotateX(-Math.PI / 2);
  return geom;
}

export const Auditorium3D: React.FC<Auditorium3DProps> = ({
  mode,
  agents,
  cameraPanMode = "auto",
  seatStatuses = {},
  seatConclusions = {},
  activeSpeakerId = null,
  selectedAgentId = null,
  onSelectAgent,
  onRunFirst,
  onRetryAgent,
  onPauseAgent,
  isSimulationRunning = false,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [webglError, setWebglError] = useState(false);
  const [hoveredTeam, setHoveredTeam] = useState<TeamId | null>(null);
  const [hoveredAgentId, setHoveredAgentId] = useState<string | null>(null);
  const [pinnedAgentId, setPinnedAgentId] = useState<string | null>(null);
  const [seatCoords, setSeatCoords] = useState<Record<string, ScreenPoint>>({});
  const [labelCoords, setLabelCoords] = useState<Record<string, ScreenPoint>>({});
  const [sliderPan, setSliderPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  const isTouchOrMobile = useMemo(() => {
    if (typeof window === "undefined") return false;
    const coarse = window.matchMedia?.("(pointer: coarse)")?.matches ?? false;
    const mobileUa = /Android|iPhone|iPad|iPod|Tablet|Mobile/i.test(navigator.userAgent || "");
    return coarse || mobileUa;
  }, []);

  const effectivePanMode: "mouse" | "slider" =
    cameraPanMode === "auto" ? (isTouchOrMobile ? "slider" : "mouse") : cameraPanMode;

  // Keep latest props in refs for the animation/raycast loop
  const hoveredAgentRef = useRef<string | null>(null);
  const pinnedAgentRef = useRef<string | null>(null);
  const selectedAgentRef = useRef<string | null>(selectedAgentId);
  const activeSpeakerRef = useRef<string | null>(activeSpeakerId);
  const seatStatusesRef = useRef<Record<string, AgentSeatStatus>>(seatStatuses);
  const modeRef = useRef<"hall" | "live">(mode);
  const effectivePanModeRef = useRef<"mouse" | "slider">(effectivePanMode);
  const sliderPanRef = useRef<{ x: number; y: number }>(sliderPan);

  hoveredAgentRef.current = hoveredAgentId;
  pinnedAgentRef.current = pinnedAgentId;
  selectedAgentRef.current = selectedAgentId;
  activeSpeakerRef.current = activeSpeakerId;
  seatStatusesRef.current = seatStatuses;
  modeRef.current = mode;
  effectivePanModeRef.current = effectivePanMode;
  sliderPanRef.current = sliderPan;

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setPinnedAgentId(null);
        setHoveredAgentId(null);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const activeAgents = useMemo(() => agents.filter((a) => a.active), [agents]);

  const { seats, wedges, dividerAngles } = useMemo(() => {
    const teams = DEFAULT_TEAMS;
    const totalSpan = MAX_ANGLE_DEG - MIN_ANGLE_DEG;

    const teamGroups = teams.map((teamId) => ({
      teamId,
      members: activeAgents.filter((a) => a.teamId === teamId),
    }));
    const weights = teamGroups.map((g) => Math.max(5.2, g.members.length + 1.8));
    const totalWeight = weights.reduce((acc, w) => acc + w, 0);

    const tierRadii = [5.6, 7.5, 9.4];
    const tierHeights = [0.18, 0.55, 0.94];

    const computedSeats: SeatPlacement[] = [];
    const computedWedges: WedgePlacement[] = [];
    const dividers: number[] = [MIN_ANGLE_DEG];

    let angleCursor = MIN_ANGLE_DEG;
    teamGroups.forEach(({ teamId, members }, idx) => {
      const wedgeSpan = (weights[idx] / totalWeight) * totalSpan;
      const a0 = angleCursor;
      const a1 = a0 + wedgeSpan;
      const aMid = (a0 + a1) / 2;
      angleCursor = a1;
      dividers.push(a1);

      const len = members.length;
      const rowCaps =
        len <= 2
          ? [len]
          : len === 3
            ? [1, 2]
            : len <= 6
              ? [1, 2, len - 3]
              : len <= 9
                ? [2, 3, len - 5]
                : [2, 4, len - 6];

      let seatCursor = 0;
      rowCaps.forEach((cap, rowIndex) => {
        const countInRow = Math.min(cap, Math.max(0, members.length - seatCursor));
        if (countInRow === 0) return;

        const tierIdx = rowCaps.length === 1 ? 1 : rowCaps.length === 2 ? rowIndex + 1 : rowIndex;
        const radius = tierRadii[tierIdx];
        const y = tierHeights[tierIdx];
        // Guarantee >= 0.48 world-unit clearance from every radial divider line
        const minClearanceDeg = (Math.asin(Math.min(0.85, 0.48 / radius)) * 180) / Math.PI;
        const marginDeg = Math.min(wedgeSpan * 0.28, minClearanceDeg);
        const usableSpan = Math.max(1.5, wedgeSpan - marginDeg * 2);

        for (let i = 0; i < countInRow; i += 1) {
          const agent = members[seatCursor];
          seatCursor += 1;
          const frac = countInRow === 1 ? 0.5 : i / (countInRow - 1);
          const seatAngle = a0 + marginDeg + frac * usableSpan;
          computedSeats.push({
            agent,
            worldPos: polarToWorld(seatAngle, radius, y),
            tierIndex: tierIdx,
          });
        }
      });

      computedWedges.push({
        teamId,
        label: TEAM_DEFINITIONS[teamId].shortLabel,
        a0,
        a1,
        aMid,
        labelWorldPos: polarToWorld(aMid, 10.65, 0.96),
      });
    });

    return { seats: computedSeats, wedges: computedWedges, dividerAngles: dividers };
  }, [activeAgents]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
    } catch {
      setWebglError(true);
      return;
    }

    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.08;
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const pmremGenerator = new THREE.PMREMGenerator(renderer);
    const envTexture = pmremGenerator.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environment = envTexture;

    const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 100);
    const baseCamPos = new THREE.Vector3(0, 8.8, 16.0);
    const lookTarget = new THREE.Vector3(0, 1.15, -1.6);
    camera.position.copy(baseCamPos);
    camera.lookAt(lookTarget);

    const spotAlphaTex = createSpotAlphaTexture();
    const stageFloorTex = createStageFloorTexture();
    const flutedWallTex = createFlutedWallTexture();
    const contactShadowTex = createContactShadowTexture();
    const surfaceBumpTex = createSurfaceBumpTexture();

    // Theme-aware materials
    const isDarkNow = () => document.documentElement.classList.contains("dark");
    const sceneBgDark = new THREE.Color(0x060a13);
    const sceneBgLight = new THREE.Color(0xe6edf5);

    const floorMat = new THREE.MeshStandardMaterial({ roughness: 0.78, metalness: 0.12 });
    const tierEvenMat = new THREE.MeshStandardMaterial({
      map: stageFloorTex,
      bumpMap: surfaceBumpTex,
      bumpScale: 0.015,
      roughness: 0.62,
      metalness: 0.22,
    });
    const tierOddMat = new THREE.MeshStandardMaterial({
      map: stageFloorTex,
      bumpMap: surfaceBumpTex,
      bumpScale: 0.015,
      roughness: 0.62,
      metalness: 0.22,
    });
    const stageMat = new THREE.MeshStandardMaterial({
      map: stageFloorTex,
      bumpMap: surfaceBumpTex,
      bumpScale: 0.012,
      roughness: 0.36,
      metalness: 0.3,
    });
    const backdropMat = new THREE.MeshStandardMaterial({
      map: flutedWallTex,
      bumpMap: flutedWallTex,
      bumpScale: 0.04,
      roughness: 0.56,
      metalness: 0.18,
    });
    const stageRimMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
    const dividerStripMat = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.85 });
    const tierTrimMat = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.5 });
    const pillarGlowMat = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.35 });
    const spotlightMat = new THREE.MeshBasicMaterial({
      transparent: true,
      opacity: 0.16,
      alphaMap: spotAlphaTex,
      side: THREE.DoubleSide,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xe0f2fe, 1.5);
    keyLight.position.set(4, 14, 9);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 1024;
    keyLight.shadow.mapSize.height = 1024;
    scene.add(keyLight);

    const rimLight = new THREE.DirectionalLight(0x818cf8, 0.85);
    rimLight.position.set(-8, 10, -8);
    scene.add(rimLight);

    const stagePointLight = new THREE.PointLight(0x38bdf8, 2.2, 18);
    stagePointLight.position.set(0, 4.2, -5.2);
    scene.add(stagePointLight);

    const applyThemeToScene = (dark: boolean) => {
      const bg = dark ? sceneBgDark : sceneBgLight;
      scene.background = bg;
      scene.fog = new THREE.FogExp2(bg.getHex(), dark ? 0.02 : 0.012);
      floorMat.color.setHex(dark ? 0x090f1d : 0xd2dce8);
      tierEvenMat.color.setHex(dark ? 0x111c33 : 0xe2e8f0);
      tierOddMat.color.setHex(dark ? 0x182744 : 0xcbd7e6);
      stageMat.color.setHex(dark ? 0x1c2d4d : 0xb8c7da);
      backdropMat.color.setHex(dark ? 0x121e36 : 0xa5b6cc);
      stageRimMat.color.setHex(dark ? 0x38bdf8 : 0x2563eb);
      dividerStripMat.color.setHex(dark ? 0x818cf8 : 0x475569);
      dividerStripMat.opacity = dark ? 0.85 : 0.72;
      tierTrimMat.color.setHex(dark ? 0x38bdf8 : 0x64748b);
      tierTrimMat.opacity = dark ? 0.42 : 0.65;
      pillarGlowMat.color.setHex(dark ? 0x38bdf8 : 0x3b82f6);
      pillarGlowMat.opacity = dark ? 0.32 : 0.28;
      spotlightMat.color.setHex(dark ? 0x38bdf8 : 0x3b82f6);
      spotlightMat.blending = dark ? THREE.AdditiveBlending : THREE.NormalBlending;
      spotlightMat.opacity = dark ? 0.14 : 0.075;
      spotlightMat.needsUpdate = true;
      ambientLight.intensity = dark ? 0.55 : 0.92;
      keyLight.intensity = dark ? 1.55 : 1.3;
      stagePointLight.intensity = dark ? 2.6 : 0.9;
      scene.environmentIntensity = dark ? 0.48 : 0.72;
    };
    applyThemeToScene(isDarkNow());

    const themeObserver = new MutationObserver(() => {
      applyThemeToScene(isDarkNow());
    });
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });

    // Seamless auditorium hall floor (eliminates circular horizon cutoff)
    const hallFloor = new THREE.Mesh(new THREE.PlaneGeometry(140, 140), floorMat);
    hallFloor.rotation.x = -Math.PI / 2;
    hallFloor.position.y = -0.02;
    hallFloor.receiveShadow = true;
    scene.add(hallFloor);

    // 3 Stepped Semi-Circular Amphitheater Tiers per Team Wedge (alternating subtle contrast)
    const tierConfigs = [
      { rIn: 4.6, rOut: 6.55, h: 0.18 },
      { rIn: 6.55, rOut: 8.45, h: 0.55 },
      { rIn: 8.45, rOut: 10.4, h: 0.94 },
    ];
    wedges.forEach((w, wIdx) => {
      const mat = wIdx % 2 === 0 ? tierEvenMat : tierOddMat;
      const aStart = wIdx === 0 ? w.a0 - 2 : w.a0;
      const aEnd = wIdx === wedges.length - 1 ? w.a1 + 2 : w.a1;
      tierConfigs.forEach((tc) => {
        const geom = buildTierSectorGeometry(tc.rIn, tc.rOut, aStart, aEnd, tc.h, 14);
        const mesh = new THREE.Mesh(geom, mat);
        mesh.position.z = ARC_CENTER_Z;
        mesh.receiveShadow = true;
        scene.add(mesh);
      });
    });

    // Stepped Tier Edge Arc Trims
    [
      { r: 4.62, y: 0.19 },
      { r: 6.55, y: 0.56 },
      { r: 8.45, y: 0.95 },
      { r: 10.38, y: 0.95 },
    ].forEach((edge) => {
      const trimGeom = buildTierSectorGeometry(edge.r - 0.025, edge.r + 0.025, MIN_ANGLE_DEG - 2, MAX_ANGLE_DEG + 2, 0.02, 48);
      const trimMesh = new THREE.Mesh(trimGeom, tierTrimMat);
      trimMesh.position.set(0, edge.y - 0.01, ARC_CENTER_Z);
      scene.add(trimMesh);
    });

    // 3D Architectural Aisle Divider Strips Between Teams (flat radial strips + upright riser plates)
    const addHorizontalAisle = (p1: THREE.Vector3, p2: THREE.Vector3) => {
      const len = p1.distanceTo(p2);
      const strip = new THREE.Mesh(new THREE.BoxGeometry(0.045, 0.022, len), dividerStripMat);
      strip.position.copy(p1).add(p2).multiplyScalar(0.5);
      strip.lookAt(p2);
      scene.add(strip);
    };
    const addVerticalRiser = (pos: THREE.Vector3, yBottom: number, yTop: number, angDeg: number) => {
      const height = Math.max(0.05, yTop - yBottom);
      const riser = new THREE.Mesh(new THREE.BoxGeometry(0.045, height, 0.03), dividerStripMat);
      riser.position.set(pos.x, (yBottom + yTop) / 2, pos.z);
      riser.rotation.y = degToRad(angDeg);
      scene.add(riser);
    };
    dividerAngles.forEach((ang) => {
      const t1a = polarToWorld(ang, 4.6, 0.19);
      const t1b = polarToWorld(ang, 6.55, 0.19);
      const t2a = polarToWorld(ang, 6.55, 0.56);
      const t2b = polarToWorld(ang, 8.45, 0.56);
      const t3a = polarToWorld(ang, 8.45, 0.95);
      const t3b = polarToWorld(ang, 10.4, 0.95);
      addHorizontalAisle(t1a, t1b);
      addVerticalRiser(t1b, 0.19, 0.56, ang);
      addHorizontalAisle(t2a, t2b);
      addVerticalRiser(t2b, 0.56, 0.95, ang);
      addHorizontalAisle(t3a, t3b);
    });

    // 3D Proscenium Stage Platform + Backstage Wall + Curved Apron + Stepped Side Stairs
    const stageMain = new THREE.Mesh(new THREE.BoxGeometry(15.2, 0.78, 4.6), stageMat);
    stageMain.position.set(0, 0.39, -6.2);
    stageMain.receiveShadow = true;
    scene.add(stageMain);

    // Backstage Architectural Proscenium Wall & Side Wing Panels
    const backWall = new THREE.Mesh(new THREE.BoxGeometry(13.6, 5.4, 0.35), backdropMat);
    backWall.position.set(0, 3.1, -8.35);
    backWall.receiveShadow = true;
    scene.add(backWall);

    [-1, 1].forEach((side) => {
      const wingWall = new THREE.Mesh(new THREE.BoxGeometry(3.2, 5.2, 0.35), backdropMat);
      wingWall.position.set(side * 7.8, 3.0, -7.4);
      wingWall.rotation.y = side * -0.42;
      scene.add(wingWall);

      const pillarGlow = new THREE.Mesh(new THREE.BoxGeometry(0.08, 4.8, 0.12), pillarGlowMat);
      pillarGlow.position.set(side * 6.55, 3.0, -8.1);
      scene.add(pillarGlow);
    });

    // Curved front stage apron
    const apronGeom = new THREE.CylinderGeometry(3.85, 4.1, 0.68, 44, 1, false, -Math.PI / 2, Math.PI);
    const apron = new THREE.Mesh(apronGeom, stageMat);
    apron.position.set(0, 0.34, -4.05);
    apron.scale.set(1.42, 1, 0.46);
    apron.receiveShadow = true;
    scene.add(apron);

    // 3D Glowing Tube Stage Edge Rim
    const rimArcPts: THREE.Vector3[] = [];
    for (let i = 0; i <= 40; i += 1) {
      const a = -Math.PI / 2 + (i / 40) * Math.PI;
      rimArcPts.push(new THREE.Vector3(Math.sin(a) * 3.92 * 1.42, 0.68, -4.05 + Math.cos(a) * 3.92 * 0.46));
    }
    const rimCurve = new THREE.CatmullRomCurve3(rimArcPts);
    const stageRimMesh = new THREE.Mesh(new THREE.TubeGeometry(rimCurve, 44, 0.032, 8, false), stageRimMat);
    scene.add(stageRimMesh);

    // Stepped side wings (left & right stairs)
    [-1, 1].forEach((side) => {
      [0, 1, 2].forEach((step) => {
        const stair = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.18, 1.3 - step * 0.22), stageMat);
        stair.position.set(side * (6.2 + step * 0.45), 0.1 + step * 0.18, -4.3 - step * 0.15);
        scene.add(stair);
      });
    });

    // Overhead Truss, 3D Spotlight Fixtures, Volumetric Cones & Stage Light Pools
    const trussMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.4, metalness: 0.75 });
    const trussBar = new THREE.Mesh(new THREE.BoxGeometry(10.5, 0.14, 0.18), trussMat);
    trussBar.position.set(0, 8.65, -5.0);
    scene.add(trussBar);

    [-3.6, 0, 3.6].forEach((sx) => {
      const fixture = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.24, 0.45, 16), trussMat);
      fixture.position.set(sx, 8.45, -5.0);
      fixture.rotation.z = sx * -0.05;
      scene.add(fixture);

      const cone = new THREE.Mesh(new THREE.ConeGeometry(2.5, 8.2, 24, 1, true), spotlightMat);
      cone.position.set(sx, 4.45, -5.0);
      cone.rotation.z = sx * -0.05;
      scene.add(cone);

      const pool = new THREE.Mesh(new THREE.CircleGeometry(1.85, 28), spotlightMat);
      pool.rotation.x = -Math.PI / 2;
      pool.position.set(sx * 0.92, 0.79, -5.0);
      scene.add(pool);
    });

    // Shared PBR materials for realistic sculpted clinicians & chairs
    const coatMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.48, metalness: 0.04 });
    const chairMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.52, metalness: 0.22 });
    const chairPadMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.65, metalness: 0.1 });
    const chromeMat = new THREE.MeshStandardMaterial({ color: 0xcbd5e1, roughness: 0.22, metalness: 0.88 });
    const pantsMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.7 });
    const shoeMat = new THREE.MeshStandardMaterial({ color: 0x090d16, roughness: 0.45, metalness: 0.15 });
    const glassesMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.25, metalness: 0.8 });
    const shadowMat = new THREE.MeshBasicMaterial({
      map: contactShadowTex,
      transparent: true,
      depthWrite: false,
    });

    const seatEntries: {
      agent: VmdtAgentConfig;
      group: THREE.Group;
      torsoGroup: THREE.Group;
      headGroup: THREE.Group;
      phaseOffset: number;
      ringMat: THREE.MeshBasicMaterial;
      beamMesh: THREE.Mesh;
      beamMat: THREE.MeshBasicMaterial;
      hitbox: THREE.Mesh;
      baseY: number;
    }[] = [];

    const hitboxes: THREE.Mesh[] = [];

    seats.forEach(({ agent, worldPos }, idx) => {
      const seatGroup = new THREE.Group();
      seatGroup.position.copy(worldPos);
      // Face toward the center of the stage (0, y, -5.2)
      seatGroup.lookAt(0, worldPos.y, -5.2);

      const built = buildRealisticClinicianMesh(agent, {
        coatMat,
        chairMat,
        chairPadMat,
        chromeMat,
        pantsMat,
        shoeMat,
        glassesMat,
        shadowMat,
      });
      seatGroup.add(built.group);

      // Floor status ring under chair
      const ringMat = new THREE.MeshBasicMaterial({
        color: STATUS_HEX.idle,
        transparent: true,
        opacity: 0.85,
        side: THREE.DoubleSide,
      });
      const ring = new THREE.Mesh(new THREE.RingGeometry(0.32, 0.41, 28), ringMat);
      ring.rotation.x = -Math.PI / 2;
      ring.position.y = 0.015;
      seatGroup.add(ring);

      // Vertical status beam (visible in live mode)
      const beamMat = new THREE.MeshBasicMaterial({
        color: STATUS_HEX.idle,
        transparent: true,
        opacity: 0,
        side: THREE.DoubleSide,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      });
      const beamMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.4, 2.8, 16, 1, true), beamMat);
      beamMesh.position.y = 1.4;
      seatGroup.add(beamMesh);

      // Invisible raycast hitbox
      const hitbox = new THREE.Mesh(
        new THREE.CylinderGeometry(0.45, 0.45, 1.25, 10),
        new THREE.MeshBasicMaterial({ visible: false })
      );
      hitbox.position.y = 0.6;
      hitbox.userData = { agentId: agent.id, teamId: agent.teamId };
      seatGroup.add(hitbox);
      hitboxes.push(hitbox);

      scene.add(seatGroup);
      seatEntries.push({
        agent,
        group: seatGroup,
        torsoGroup: built.torsoGroup,
        headGroup: built.headGroup,
        phaseOffset: idx * 0.45,
        ringMat,
        beamMesh,
        beamMat,
        hitbox,
        baseY: worldPos.y,
      });
    });

    // Mouse parallax & raycasting
    const raycaster = new THREE.Raycaster();
    const pointerNdc = new THREE.Vector2(-99, -99);
    let targetParallaxX = 0;
    let targetParallaxY = 0;
    let targetNormX = 0;

    const handlePointerMove = (e: PointerEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const ny = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      pointerNdc.set(nx, ny);
      if (effectivePanModeRef.current === "mouse") {
        targetNormX = nx;
        targetParallaxX = nx * 16.0;
        targetParallaxY = ny * 2.8;
      }

      raycaster.setFromCamera(pointerNdc, camera);
      const hits = raycaster.intersectObjects(hitboxes, false);
      if (hits.length > 0) {
        const { agentId, teamId } = hits[0].object.userData as { agentId: string; teamId: TeamId };
        setHoveredAgentId(agentId);
        setHoveredTeam(teamId);
        renderer.domElement.style.cursor = "pointer";
      } else {
        setHoveredAgentId(null);
        setHoveredTeam(null);
        renderer.domElement.style.cursor = "default";
      }
    };

    const handlePointerClick = (e: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const ny = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(new THREE.Vector2(nx, ny), camera);
      const hits = raycaster.intersectObjects(hitboxes, false);
      if (hits.length > 0) {
        const { agentId } = hits[0].object.userData as { agentId: string };
        setPinnedAgentId((prev) => (prev === agentId ? null : agentId));
        onSelectAgent?.(agentId);
      } else {
        setPinnedAgentId(null);
      }
    };

    const handlePointerLeave = () => {
      targetNormX = 0;
      targetParallaxX = 0;
      targetParallaxY = 0;
    };

    const domEl = renderer.domElement;
    domEl.addEventListener("pointermove", handlePointerMove);
    domEl.addEventListener("pointerleave", handlePointerLeave);
    domEl.addEventListener("click", handlePointerClick);

    const resizeObserver = new ResizeObserver(() => {
      if (!container) return;
      const w = container.clientWidth || window.innerWidth;
      const h = container.clientHeight || window.innerHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    });
    resizeObserver.observe(container);

    let rafId = 0;
    let frameCount = 0;
    const projVec = new THREE.Vector3();
    const currentLook = lookTarget.clone();

    const animate = (timeMs: number) => {
      rafId = requestAnimationFrame(animate);
      const t = timeMs * 0.001;

      // Full wing-to-center orbital pan: driven by mouse hover OR touch/slider controls
      if (effectivePanModeRef.current === "slider") {
        targetNormX = sliderPanRef.current.x;
        targetParallaxX = sliderPanRef.current.x * 16.0;
        targetParallaxY = sliderPanRef.current.y * 2.8;
      }
      const targetCamX = baseCamPos.x + targetParallaxX;
      const targetCamY = Math.max(4.6, baseCamPos.y + targetParallaxY);
      const targetCamZ = baseCamPos.z - Math.abs(targetNormX) * 4.5;
      camera.position.x += (targetCamX - camera.position.x) * 0.065;
      camera.position.y += (targetCamY - camera.position.y) * 0.065;
      camera.position.z += (targetCamZ - camera.position.z) * 0.065;
      currentLook.x += (lookTarget.x + targetNormX * 10.2 - currentLook.x) * 0.065;
      currentLook.y += (lookTarget.y + targetParallaxY * 0.16 - currentLook.y) * 0.065;
      camera.lookAt(currentLook);

      // Update seat status rings, beams, and hover lift
      const curMode = modeRef.current;
      const curSpeaker = activeSpeakerRef.current;
      const curStatuses = seatStatusesRef.current;
      const curHovered = hoveredAgentRef.current;
      const curPinned = pinnedAgentRef.current;

      seatEntries.forEach((entry) => {
        const rawStatus: AgentSeatStatus =
          curMode === "hall"
            ? "idle"
            : curSpeaker === entry.agent.id
              ? "running"
              : curStatuses[entry.agent.id] || "queued";

        entry.ringMat.color.setHex(STATUS_HEX[rawStatus]);
        const isHighlighted =
          curHovered === entry.agent.id ||
          curPinned === entry.agent.id ||
          selectedAgentRef.current === entry.agent.id;
        const isSpeaker = curMode === "live" && rawStatus === "running";

        const targetY = entry.baseY + (isHighlighted ? 0.14 : isSpeaker ? Math.sin(t * 4) * 0.05 + 0.08 : 0);
        entry.group.position.y += (targetY - entry.group.position.y) * 0.14;

        const targetScale = isHighlighted ? 0.96 : isSpeaker ? 0.92 : 0.84;
        entry.group.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.14);

        // Subtle realistic idle breathing & gentle head micro-turns
        const p = t + entry.phaseOffset;
        entry.torsoGroup.scale.y = 1 + Math.sin(p * 1.6) * 0.014;
        entry.headGroup.rotation.y = Math.sin(p * 0.55) * (isSpeaker ? 0.14 : 0.06);
        entry.headGroup.rotation.x = Math.cos(p * 0.7) * 0.025;

        if (curMode === "live") {
          entry.beamMat.color.setHex(STATUS_HEX[rawStatus]);
          entry.beamMat.opacity = isSpeaker ? 0.24 + Math.sin(t * 5) * 0.08 : rawStatus === "completed" || rawStatus === "failed" ? 0.12 : 0.04;
        } else {
          entry.beamMat.opacity = isHighlighted ? 0.14 : 0;
        }
      });

      renderer.render(scene, camera);

      // Project 3D coordinates to 2D screen positions for HTML labels & popover (every 2 frames)
      frameCount += 1;
      if (frameCount % 2 === 0 || frameCount === 1) {
        const w = container.clientWidth || 1;
        const h = container.clientHeight || 1;

        const nextSeats: Record<string, ScreenPoint> = {};
        seatEntries.forEach((entry) => {
          projVec.copy(entry.group.position);
          projVec.y += 1.25;
          projVec.project(camera);
          nextSeats[entry.agent.id] = {
            x: ((projVec.x + 1) / 2) * w,
            y: ((-projVec.y + 1) / 2) * h,
          };
        });
        setSeatCoords(nextSeats);

        const nextLabels: Record<string, ScreenPoint> = {};
        wedges.forEach((wedge) => {
          projVec.copy(wedge.labelWorldPos);
          projVec.project(camera);
          nextLabels[wedge.teamId] = {
            x: ((projVec.x + 1) / 2) * w,
            y: ((-projVec.y + 1) / 2) * h,
          };
        });
        setLabelCoords(nextLabels);
      }
    };

    rafId = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(rafId);
      themeObserver.disconnect();
      resizeObserver.disconnect();
      domEl.removeEventListener("pointermove", handlePointerMove);
      domEl.removeEventListener("pointerleave", handlePointerLeave);
      domEl.removeEventListener("click", handlePointerClick);
      pmremGenerator.dispose();
      envTexture.dispose();
      renderer.dispose();
      if (domEl.parentNode === container) {
        container.removeChild(domEl);
      }
    };
  }, [seats, wedges, dividerAngles, onSelectAgent]);

  const activePopoverId = pinnedAgentId ?? hoveredAgentId;
  const activeAgent = activeAgents.find((a) => a.id === activePopoverId) || null;
  const activePoint = activeAgent ? seatCoords[activeAgent.id] : null;

  const containerRect = containerRef.current?.getBoundingClientRect();
  const winW = typeof window !== "undefined" ? window.innerWidth : 1280;
  const absX = activePoint ? (containerRect?.left ?? 0) + activePoint.x : 0;
  const absY = activePoint ? (containerRect?.top ?? 0) + activePoint.y : 0;
  const popoverLeft = Math.min(Math.max(absX, 160), winW - 160);
  const flipBelow = absY < 270;
  const popoverTop = flipBelow ? Math.max(absY + 26, 68) : absY - 16;

  const popoverNode = (
    <AnimatePresence>
      {activeAgent && activePoint && (
        <motion.div
          key={activeAgent.id}
          initial={{ opacity: 0, y: flipBelow ? -6 : 6, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: flipBelow ? -4 : 4, scale: 0.96 }}
          transition={{ duration: 0.14 }}
          style={{
            left: `${popoverLeft}px`,
            top: `${popoverTop}px`,
          }}
          onClick={(e) => e.stopPropagation()}
          className={`pointer-events-auto fixed z-[9999] w-[300px] -translate-x-1/2 ${
            flipBelow ? "" : "-translate-y-full"
          } rounded-xl border border-slate-200/95 bg-white/95 p-3 shadow-2xl backdrop-blur-md dark:border-sky-400/35 dark:bg-slate-900/95 dark:shadow-[0_12px_40px_rgba(2,6,23,0.9)]`}
        >
          <div className="flex items-start justify-between gap-2.5">
            <div className="flex items-center gap-2.5">
              <div className="h-10 w-10 shrink-0 rounded-lg bg-slate-100 p-0.5 dark:bg-slate-800">
                <DoctorAvatar
                  variant={activeAgent.avatarVariant}
                  scrubColor={activeAgent.scrubColor}
                  hasGlasses={activeAgent.hasGlasses}
                  propType={activeAgent.propType}
                  size={36}
                />
              </div>
              <div>
                <p className="text-xs font-bold leading-tight text-slate-900 dark:text-slate-50">
                  {activeAgent.displayName}
                </p>
                <p className="text-[11px] font-medium text-blue-600 dark:text-sky-400">
                  {activeAgent.specialty}
                </p>
              </div>
            </div>
            {pinnedAgentId === activeAgent.id && (
              <button
                type="button"
                aria-label="Close agent card"
                onClick={() => setPinnedAgentId(null)}
                className="rounded p-0.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          <div className="mt-2 rounded-lg bg-slate-50 px-2.5 py-1.5 text-[11px] text-slate-600 dark:bg-slate-800/75 dark:text-slate-300">
            <p className="line-clamp-3 leading-snug">
              <span className="font-semibold text-slate-700 dark:text-slate-200">Stance: </span>
              {activeAgent.personalitySummary}
            </p>
          </div>

          {mode === "live" && (
            <div className="mt-2 space-y-2 border-t border-slate-200/70 pt-2 dark:border-slate-700/70">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-slate-500 dark:text-slate-400">Live Status</span>
                <span className="inline-flex items-center gap-1 font-semibold capitalize text-slate-800 dark:text-slate-100">
                  {(activeSpeakerId === activeAgent.id ||
                    seatStatuses[activeAgent.id] === "running") && (
                    <Sparkles className="h-3 w-3 text-sky-400" />
                  )}
                  {seatStatuses[activeAgent.id] === "failed" && (
                    <AlertCircle className="h-3 w-3 text-rose-500" />
                  )}
                  {activeSpeakerId === activeAgent.id
                    ? "active speaker"
                    : STATUS_LABEL[seatStatuses[activeAgent.id] || "queued"]}
                </span>
              </div>
              {seatConclusions[activeAgent.id] && (
                <p className="line-clamp-2 text-[11px] leading-snug text-slate-600 dark:text-slate-300">
                  {seatConclusions[activeAgent.id]}
                </p>
              )}
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  disabled={!isSimulationRunning}
                  onClick={() => onRunFirst?.(activeAgent.id)}
                  className="inline-flex flex-1 items-center justify-center gap-1 rounded-md bg-emerald-500/15 px-2 py-1 text-[11px] font-semibold text-emerald-700 hover:bg-emerald-500/25 disabled:opacity-45 dark:text-emerald-300"
                >
                  <Play className="h-3 w-3" />
                  Run First
                </button>
                <button
                  type="button"
                  onClick={() => onRetryAgent?.(activeAgent.id)}
                  className="inline-flex flex-1 items-center justify-center gap-1 rounded-md bg-blue-500/15 px-2 py-1 text-[11px] font-semibold text-blue-700 hover:bg-blue-500/25 dark:text-sky-300"
                >
                  <RotateCcw className="h-3 w-3" />
                  Retry
                </button>
                <button
                  type="button"
                  onClick={() => onPauseAgent?.(activeAgent.id)}
                  className="inline-flex flex-1 items-center justify-center gap-1 rounded-md bg-slate-500/15 px-2 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-500/25 dark:text-slate-300"
                >
                  <Pause className="h-3 w-3" />
                  Pause
                </button>
              </div>
            </div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );

  return (
    <div className="relative h-full w-full overflow-hidden select-none isolate">
      {/* Three.js WebGL Canvas Mount */}
      <div ref={containerRef} className="absolute inset-0 h-full w-full" />

      {webglError && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80 text-sm text-slate-200">
          3D WebGL view is unavailable in this browser context.
        </div>
      )}

      {/* 3D-Projected Specialty Team Labels Along Outer Auditorium Rim */}
      {wedges.map((w) => {
        const pt = labelCoords[w.teamId];
        if (!pt) return null;
        const isHot = hoveredTeam === w.teamId;
        const rot = -w.aMid * 0.28;
        return (
          <div
            key={w.teamId}
            style={{
              left: `${pt.x}px`,
              top: `${pt.y}px`,
              transform: `translate(-50%, -50%) rotate(${rot}deg)`,
            }}
            className={`pointer-events-none absolute z-20 whitespace-nowrap rounded-full px-2.5 py-0.5 text-[10px] font-semibold tracking-wide transition-colors duration-200 sm:text-[11px] ${
              isHot
                ? "bg-blue-600/20 text-blue-700 dark:bg-sky-400/25 dark:text-sky-200 shadow-sm"
                : "text-slate-700/90 dark:text-indigo-200/85"
            }`}
          >
            {w.label}
          </div>
        );
      })}

      {/* Compact Floating Camera Pan Sliders (Active on Mobile/Tablet Auto or Slider Mode) */}
      {effectivePanMode === "slider" && (
        <div
          onClick={(e) => e.stopPropagation()}
          className="pointer-events-auto absolute bottom-3 left-1/2 z-30 flex -translate-x-1/2 flex-wrap items-center gap-3 rounded-2xl border border-slate-200/90 bg-white/85 px-3.5 py-2 text-[11px] shadow-lg backdrop-blur-md dark:border-sky-400/25 dark:bg-slate-900/85"
        >
          <label className="flex items-center gap-2 font-medium text-slate-700 dark:text-slate-200">
            <span>Pan</span>
            <input
              type="range"
              aria-label="Horizontal camera pan"
              min={-1}
              max={1}
              step={0.02}
              value={sliderPan.x}
              onChange={(e) => setSliderPan((p) => ({ ...p, x: Number(e.target.value) }))}
              className="w-24 accent-blue-600 dark:accent-sky-400 sm:w-32"
            />
          </label>
          <label className="flex items-center gap-2 font-medium text-slate-700 dark:text-slate-200">
            <span>Tilt</span>
            <input
              type="range"
              aria-label="Vertical camera tilt"
              min={-1}
              max={1}
              step={0.02}
              value={sliderPan.y}
              onChange={(e) => setSliderPan((p) => ({ ...p, y: Number(e.target.value) }))}
              className="w-20 accent-blue-600 dark:accent-sky-400 sm:w-24"
            />
          </label>
          {(sliderPan.x !== 0 || sliderPan.y !== 0) && (
            <button
              type="button"
              onClick={() => setSliderPan({ x: 0, y: 0 })}
              className="inline-flex items-center gap-1 rounded-lg bg-slate-200/80 px-2 py-1 text-[10px] font-semibold text-slate-700 hover:bg-slate-300/80 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              <RotateCcw className="h-3 w-3" />
              Center
            </button>
          )}
        </div>
      )}

      {/* Floating Glassmorphic Agent Popover Portaled to document.body at z-[9999] */}
      {typeof document !== "undefined" ? createPortal(popoverNode, document.body) : popoverNode}
    </div>
  );
};

export default Auditorium3D;
