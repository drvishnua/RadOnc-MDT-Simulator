import React, { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, Pause, Play, RotateCcw, Sparkles, X } from "lucide-react";
import DoctorAvatar from "./DoctorAvatar.js";
import { TEAM_DEFINITIONS } from "../../utils/vmdtRoster.js";
import {
  DEFAULT_TEAMS,
  type AgentSeatStatus,
  type TeamId,
  type VmdtAgentConfig,
} from "../../virtualMdtTypes.js";

export interface Auditorium3DProps {
  mode: "hall" | "live";
  agents: VmdtAgentConfig[];
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

const SKIN_TONES = ["#F5CBA7", "#E0AC69", "#C68642", "#8D5524", "#FAD7A0", "#D5A078", "#A5694F", "#F1C27D"];
const HAIR_COLORS = ["#1E293B", "#4A3728", "#0F172A", "#6D4C3D", "#94A3B8", "#3B2F2F", "#2C222B", "#7C4D3A"];

function buildClinicianMesh(
  agent: VmdtAgentConfig,
  coatMat: THREE.MeshStandardMaterial,
  accentMat: THREE.MeshStandardMaterial,
  skinMat: THREE.MeshStandardMaterial,
  hairMat: THREE.MeshStandardMaterial,
  chairMat: THREE.MeshStandardMaterial,
  metalMat: THREE.MeshStandardMaterial,
  pantsMat: THREE.MeshStandardMaterial
): THREE.Group {
  const group = new THREE.Group();

  // Pedestal base + stem
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.24, 0.05, 16), metalMat);
  base.position.y = 0.025;
  group.add(base);

  const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.05, 0.22, 10), metalMat);
  stem.position.y = 0.14;
  group.add(stem);

  // Chair seat cushion
  const seatCushion = new THREE.Mesh(new THREE.BoxGeometry(0.46, 0.08, 0.44), chairMat);
  seatCushion.position.set(0, 0.27, 0.02);
  seatCushion.castShadow = true;
  group.add(seatCushion);

  // Chair backrest (behind seated clinician, i.e., -z in local space where +z faces stage)
  const backrest = new THREE.Mesh(new THREE.BoxGeometry(0.44, 0.48, 0.08), chairMat);
  backrest.position.set(0, 0.54, -0.18);
  backrest.rotation.x = -0.1;
  backrest.castShadow = true;
  group.add(backrest);

  // Armrests
  const armGeom = new THREE.BoxGeometry(0.06, 0.05, 0.34);
  const leftArm = new THREE.Mesh(armGeom, chairMat);
  leftArm.position.set(-0.24, 0.42, -0.02);
  const rightArm = new THREE.Mesh(armGeom, chairMat);
  rightArm.position.set(0.24, 0.42, -0.02);
  group.add(leftArm, rightArm);

  // Seated legs (thighs forward + calves down toward +z)
  const thighGeom = new THREE.CylinderGeometry(0.065, 0.06, 0.3, 10);
  thighGeom.rotateX(Math.PI / 2);
  const leftThigh = new THREE.Mesh(thighGeom, pantsMat);
  leftThigh.position.set(-0.1, 0.34, 0.14);
  const rightThigh = new THREE.Mesh(thighGeom, pantsMat);
  rightThigh.position.set(0.1, 0.34, 0.14);
  group.add(leftThigh, rightThigh);

  const calfGeom = new THREE.CylinderGeometry(0.055, 0.048, 0.28, 10);
  const leftCalf = new THREE.Mesh(calfGeom, pantsMat);
  leftCalf.position.set(-0.1, 0.2, 0.28);
  const rightCalf = new THREE.Mesh(calfGeom, pantsMat);
  rightCalf.position.set(0.1, 0.2, 0.28);
  group.add(leftCalf, rightCalf);

  // Torso (lab coat or scrubs based on variant)
  const torsoMat = agent.avatarVariant % 3 === 1 ? accentMat : coatMat;
  const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.19, 0.44, 14), torsoMat);
  torso.position.set(0, 0.56, 0.0);
  torso.castShadow = true;
  group.add(torso);

  // Inner scrub/shirt collar accent
  const collar = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.11, 0.12, 12), accentMat);
  collar.position.set(0, 0.74, 0.03);
  group.add(collar);

  // Shoulders & arms
  const upperArmGeom = new THREE.CylinderGeometry(0.048, 0.044, 0.28, 10);
  const leftUpperArm = new THREE.Mesh(upperArmGeom, torsoMat);
  leftUpperArm.position.set(-0.21, 0.58, 0.04);
  leftUpperArm.rotation.z = 0.15;
  leftUpperArm.rotation.x = -0.35;
  const rightUpperArm = new THREE.Mesh(upperArmGeom, torsoMat);
  rightUpperArm.position.set(0.21, 0.58, 0.04);
  rightUpperArm.rotation.z = -0.15;
  rightUpperArm.rotation.x = -0.35;
  group.add(leftUpperArm, rightUpperArm);

  // Head
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.145, 16, 16), skinMat);
  head.position.set(0, 0.92, 0.02);
  head.castShadow = true;
  group.add(head);

  // Hair cap
  const hair = new THREE.Mesh(
    new THREE.SphereGeometry(0.152, 16, 12, 0, Math.PI * 2, 0, Math.PI * 0.58),
    hairMat
  );
  hair.position.set(0, 0.94, 0.0);
  hair.rotation.x = -0.22;
  group.add(hair);

  // Optional tablet prop in lap for variety
  if (agent.propType === "tablet") {
    const tablet = new THREE.Mesh(
      new THREE.BoxGeometry(0.2, 0.015, 0.14),
      new THREE.MeshStandardMaterial({ color: 0x0f172a, emissive: 0x38bdf8, emissiveIntensity: 0.35 })
    );
    tablet.position.set(0, 0.44, 0.22);
    tablet.rotation.x = -0.35;
    group.add(tablet);
  }

  return group;
}

export const Auditorium3D: React.FC<Auditorium3DProps> = ({
  mode,
  agents,
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

  // Keep latest props in refs for the animation/raycast loop
  const hoveredAgentRef = useRef<string | null>(null);
  const pinnedAgentRef = useRef<string | null>(null);
  const selectedAgentRef = useRef<string | null>(selectedAgentId);
  const activeSpeakerRef = useRef<string | null>(activeSpeakerId);
  const seatStatusesRef = useRef<Record<string, AgentSeatStatus>>(seatStatuses);
  const modeRef = useRef<"hall" | "live">(mode);

  hoveredAgentRef.current = hoveredAgentId;
  pinnedAgentRef.current = pinnedAgentId;
  selectedAgentRef.current = selectedAgentId;
  activeSpeakerRef.current = activeSpeakerId;
  seatStatusesRef.current = seatStatuses;
  modeRef.current = mode;

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
    const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 100);
    const baseCamPos = new THREE.Vector3(0, 8.8, 16.0);
    const lookTarget = new THREE.Vector3(0, 1.15, -1.6);
    camera.position.copy(baseCamPos);
    camera.lookAt(lookTarget);

    // Soft vertical gradient alpha map for volumetric spotlight cones
    const spotCanvas = document.createElement("canvas");
    spotCanvas.width = 4;
    spotCanvas.height = 128;
    const spotCtx = spotCanvas.getContext("2d");
    if (spotCtx) {
      const grad = spotCtx.createLinearGradient(0, 0, 0, 128);
      grad.addColorStop(0, "#ffffff");
      grad.addColorStop(0.55, "#888888");
      grad.addColorStop(1, "#000000");
      spotCtx.fillStyle = grad;
      spotCtx.fillRect(0, 0, 4, 128);
    }
    const spotAlphaTex = new THREE.CanvasTexture(spotCanvas);

    // Theme-aware materials
    const isDarkNow = () => document.documentElement.classList.contains("dark");
    const sceneBgDark = new THREE.Color(0x070b14);
    const sceneBgLight = new THREE.Color(0xeef3f9);

    const floorMat = new THREE.MeshStandardMaterial({ roughness: 0.72, metalness: 0.18 });
    const stageMat = new THREE.MeshStandardMaterial({ roughness: 0.45, metalness: 0.25 });
    const stageRimMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
    const dividerMat = new THREE.LineBasicMaterial({ transparent: true, opacity: 0.55 });
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
      scene.fog = new THREE.FogExp2(bg.getHex(), dark ? 0.022 : 0.015);
      floorMat.color.setHex(dark ? 0x0f172a : 0xdbe4ef);
      stageMat.color.setHex(dark ? 0x111c33 : 0xf8fafc);
      stageRimMat.color.setHex(dark ? 0x38bdf8 : 0x2563eb);
      dividerMat.color.setHex(dark ? 0x818cf8 : 0x64748b);
      dividerMat.opacity = dark ? 0.52 : 0.38;
      spotlightMat.color.setHex(dark ? 0x38bdf8 : 0x60a5fa);
      spotlightMat.opacity = dark ? 0.11 : 0.08;
      ambientLight.intensity = dark ? 0.65 : 1.05;
      keyLight.intensity = dark ? 1.45 : 1.25;
      stagePointLight.intensity = dark ? 2.4 : 0.9;
    };
    applyThemeToScene(isDarkNow());

    const themeObserver = new MutationObserver(() => {
      applyThemeToScene(isDarkNow());
    });
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });

    // Base auditorium hall floor
    const hallFloor = new THREE.Mesh(new THREE.CircleGeometry(24, 48), floorMat);
    hallFloor.rotation.x = -Math.PI / 2;
    hallFloor.position.y = -0.02;
    hallFloor.receiveShadow = true;
    scene.add(hallFloor);

    // 3 Stepped Semi-Circular Amphitheater Tiers
    const tierConfigs = [
      { rIn: 4.6, rOut: 6.55, h: 0.18 },
      { rIn: 6.55, rOut: 8.45, h: 0.55 },
      { rIn: 8.45, rOut: 10.4, h: 0.94 },
    ];
    tierConfigs.forEach((tc) => {
      const geom = buildTierSectorGeometry(tc.rIn, tc.rOut, MIN_ANGLE_DEG - 2, MAX_ANGLE_DEG + 2, tc.h, 44);
      const mesh = new THREE.Mesh(geom, floorMat);
      mesh.receiveShadow = true;
      scene.add(mesh);
    });

    // Radial Wedge Divider Lines
    dividerAngles.forEach((ang) => {
      const pts = [
        polarToWorld(ang, 4.6, 0.2),
        polarToWorld(ang, 6.55, 0.57),
        polarToWorld(ang, 8.45, 0.96),
        polarToWorld(ang, 10.4, 0.96),
      ];
      const lineGeom = new THREE.BufferGeometry().setFromPoints(pts);
      const line = new THREE.Line(lineGeom, dividerMat);
      scene.add(line);
    });

    // 3D Stage Platform + Curved Semi-Circular Stage Apron + Stepped Side Stairs
    const stageMain = new THREE.Mesh(new THREE.BoxGeometry(14.6, 0.75, 4.4), stageMat);
    stageMain.position.set(0, 0.375, -6.2);
    stageMain.receiveShadow = true;
    scene.add(stageMain);

    // Curved front stage lip
    const apronGeom = new THREE.CylinderGeometry(3.8, 4.05, 0.65, 40, 1, false, -Math.PI / 2, Math.PI);
    const apron = new THREE.Mesh(apronGeom, stageMat);
    apron.position.set(0, 0.325, -4.1);
    apron.scale.set(1.35, 1, 0.45);
    apron.receiveShadow = true;
    scene.add(apron);

    // Glowing stage edge rim
    const rimArcPts: THREE.Vector3[] = [];
    for (let i = 0; i <= 36; i += 1) {
      const a = -Math.PI / 2 + (i / 36) * Math.PI;
      rimArcPts.push(new THREE.Vector3(Math.sin(a) * 3.9 * 1.35, 0.66, -4.1 + Math.cos(a) * 3.9 * 0.45));
    }
    const stageRimLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints(rimArcPts), stageRimMat);
    scene.add(stageRimLine);

    // Stepped side wings (left & right stairs)
    [-1, 1].forEach((side) => {
      [0, 1, 2].forEach((step) => {
        const stair = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.18, 1.3 - step * 0.22), stageMat);
        stair.position.set(side * (6.2 + step * 0.45), 0.1 + step * 0.18, -4.3 - step * 0.15);
        scene.add(stair);
      });
    });

    // Overhead Volumetric Spotlight Cones
    [-3.6, 0, 3.6].forEach((sx) => {
      const cone = new THREE.Mesh(new THREE.ConeGeometry(2.6, 8.5, 24, 1, true), spotlightMat);
      cone.position.set(sx, 4.5, -5.0);
      cone.rotation.z = sx * -0.05;
      scene.add(cone);
    });

    // Shared materials for clinicians
    const coatMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.55 });
    const chairMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.65, metalness: 0.15 });
    const metalMat = new THREE.MeshStandardMaterial({ color: 0x64748b, roughness: 0.35, metalness: 0.7 });
    const pantsMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.7 });

    const seatEntries: {
      agent: VmdtAgentConfig;
      group: THREE.Group;
      ringMat: THREE.MeshBasicMaterial;
      beamMesh: THREE.Mesh;
      beamMat: THREE.MeshBasicMaterial;
      hitbox: THREE.Mesh;
      baseY: number;
    }[] = [];

    const hitboxes: THREE.Mesh[] = [];

    seats.forEach(({ agent, worldPos }) => {
      const seatGroup = new THREE.Group();
      seatGroup.position.copy(worldPos);
      // Face toward the center of the stage (0, y, -5.2)
      seatGroup.lookAt(0, worldPos.y, -5.2);

      const variantIdx = Math.abs(agent.avatarVariant || 0) % 8;
      const accentMat = new THREE.MeshStandardMaterial({
        color: new THREE.Color(agent.scrubColor || "#0284c7"),
        roughness: 0.55,
      });
      const skinMat = new THREE.MeshStandardMaterial({
        color: new THREE.Color(SKIN_TONES[variantIdx]),
        roughness: 0.65,
      });
      const hairMat = new THREE.MeshStandardMaterial({
        color: new THREE.Color(HAIR_COLORS[variantIdx]),
        roughness: 0.75,
      });

      const clinician = buildClinicianMesh(
        agent,
        coatMat,
        accentMat,
        skinMat,
        hairMat,
        chairMat,
        metalMat,
        pantsMat
      );
      seatGroup.add(clinician);

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

    const handlePointerMove = (e: PointerEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const ny = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      pointerNdc.set(nx, ny);
      targetParallaxX = nx * 0.45;
      targetParallaxY = ny * 0.18;

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

    const domEl = renderer.domElement;
    domEl.addEventListener("pointermove", handlePointerMove);
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

    const animate = (timeMs: number) => {
      rafId = requestAnimationFrame(animate);
      const t = timeMs * 0.001;

      // Smooth camera parallax
      camera.position.x += (baseCamPos.x + targetParallaxX - camera.position.x) * 0.06;
      camera.position.y += (baseCamPos.y + targetParallaxY - camera.position.y) * 0.06;
      camera.lookAt(lookTarget);

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
      domEl.removeEventListener("click", handlePointerClick);
      renderer.dispose();
      if (domEl.parentNode === container) {
        container.removeChild(domEl);
      }
    };
  }, [seats, wedges, dividerAngles, onSelectAgent]);

  const activePopoverId = pinnedAgentId ?? hoveredAgentId;
  const activeAgent = activeAgents.find((a) => a.id === activePopoverId) || null;
  const activePoint = activeAgent ? seatCoords[activeAgent.id] : null;

  const containerW = containerRef.current?.clientWidth || 1200;
  const popoverLeft = activePoint ? Math.min(Math.max(activePoint.x, 155), containerW - 155) : 0;
  const popoverTop = activePoint ? Math.max(activePoint.y - 16, 125) : 0;

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

      {/* Floating Glassmorphic Agent Popover (Always above all seats & stage overlays at z-[999]) */}
      <AnimatePresence>
        {activeAgent && activePoint && (
          <motion.div
            key={activeAgent.id}
            initial={{ opacity: 0, y: 6, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.96 }}
            transition={{ duration: 0.14 }}
            style={{
              left: `${popoverLeft}px`,
              top: `${popoverTop}px`,
            }}
            onClick={(e) => e.stopPropagation()}
            className="pointer-events-auto absolute z-[999] w-[290px] -translate-x-1/2 -translate-y-full rounded-xl border border-slate-200/95 bg-white/95 p-3 shadow-2xl backdrop-blur-md dark:border-sky-400/35 dark:bg-slate-900/95 dark:shadow-[0_12px_40px_rgba(2,6,23,0.9)]"
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
                  <p className="text-xs font-bold text-slate-900 dark:text-slate-50 leading-tight">
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
              <span className="font-semibold text-slate-700 dark:text-slate-200">Stance: </span>
              {activeAgent.personalitySummary}
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
    </div>
  );
};

export default Auditorium3D;
