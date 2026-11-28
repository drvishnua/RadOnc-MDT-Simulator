import * as THREE from "three";
import type { VmdtAgentConfig } from "../../virtualMdtTypes.js";

export const SKIN_TONES = [
  "#F5CBA7",
  "#E0AC69",
  "#C68642",
  "#8D5524",
  "#FAD7A0",
  "#D5A078",
  "#A5694F",
  "#F1C27D",
];

export const HAIR_COLORS = [
  "#1E293B",
  "#4A3728",
  "#0F172A",
  "#6D4C3D",
  "#94A3B8",
  "#3B2F2F",
  "#2C222B",
  "#7C4D3A",
];

export function createSpotAlphaTexture(): THREE.CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = 4;
  canvas.height = 128;
  const ctx = canvas.getContext("2d");
  if (ctx) {
    const grad = ctx.createLinearGradient(0, 0, 0, 128);
    grad.addColorStop(0, "#ffffff");
    grad.addColorStop(0.55, "#888888");
    grad.addColorStop(1, "#000000");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 4, 128);
  }
  return new THREE.CanvasTexture(canvas);
}

export function createContactShadowTexture(): THREE.CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = 64;
  canvas.height = 64;
  const ctx = canvas.getContext("2d");
  if (ctx) {
    const grad = ctx.createRadialGradient(32, 32, 4, 32, 32, 30);
    grad.addColorStop(0, "rgba(2, 6, 23, 0.52)");
    grad.addColorStop(0.55, "rgba(2, 6, 23, 0.22)");
    grad.addColorStop(1, "rgba(2, 6, 23, 0)");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 64, 64);
  }
  return new THREE.CanvasTexture(canvas);
}

export function createStageFloorTexture(): THREE.CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext("2d");
  if (ctx) {
    const grad = ctx.createRadialGradient(256, 256, 30, 256, 256, 360);
    grad.addColorStop(0, "#f8fafc");
    grad.addColorStop(0.6, "#e2e8f0");
    grad.addColorStop(1, "#cbd5e1");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 512, 512);

    // Subtle brushed architectural grain + tile seams
    for (let y = 0; y < 512; y += 4) {
      ctx.fillStyle = y % 8 === 0 ? "rgba(255,255,255,0.045)" : "rgba(15,23,42,0.035)";
      ctx.fillRect(0, y, 512, 2);
    }
    ctx.strokeStyle = "rgba(51, 65, 85, 0.16)";
    ctx.lineWidth = 1.5;
    for (let i = 0; i <= 512; i += 128) {
      ctx.beginPath();
      ctx.moveTo(i, 0);
      ctx.lineTo(i, 512);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, i);
      ctx.lineTo(512, i);
      ctx.stroke();
    }
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(8, 8);
  return tex;
}

export function createFlutedWallTexture(): THREE.CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 256;
  const ctx = canvas.getContext("2d");
  if (ctx) {
    const vGrad = ctx.createLinearGradient(0, 0, 0, 256);
    vGrad.addColorStop(0, "#94a3b8");
    vGrad.addColorStop(0.45, "#e2e8f0");
    vGrad.addColorStop(1, "#64748b");
    ctx.fillStyle = vGrad;
    ctx.fillRect(0, 0, 512, 256);

    for (let x = 0; x < 512; x += 20) {
      const slat = ctx.createLinearGradient(x, 0, x + 20, 0);
      slat.addColorStop(0, "rgba(15, 23, 42, 0.34)");
      slat.addColorStop(0.35, "rgba(255, 255, 255, 0.18)");
      slat.addColorStop(0.7, "rgba(15, 23, 42, 0.12)");
      slat.addColorStop(1, "rgba(15, 23, 42, 0.36)");
      ctx.fillStyle = slat;
      ctx.fillRect(x, 0, 20, 256);
    }
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.ClampToEdgeWrapping;
  tex.repeat.set(6, 1);
  return tex;
}

export function createSurfaceBumpTexture(): THREE.CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext("2d");
  if (ctx) {
    ctx.fillStyle = "#808080";
    ctx.fillRect(0, 0, 256, 256);
    ctx.strokeStyle = "#404040";
    ctx.lineWidth = 2;
    for (let i = 0; i <= 256; i += 64) {
      ctx.beginPath();
      ctx.moveTo(i, 0);
      ctx.lineTo(i, 256);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, i);
      ctx.lineTo(256, i);
      ctx.stroke();
    }
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(10, 10);
  return tex;
}

export interface BuiltClinician {
  group: THREE.Group;
  torsoGroup: THREE.Group;
  headGroup: THREE.Group;
}

export function buildRealisticClinicianMesh(
  agent: VmdtAgentConfig,
  shared: {
    coatMat: THREE.MeshStandardMaterial;
    chairMat: THREE.MeshStandardMaterial;
    chairPadMat: THREE.MeshStandardMaterial;
    chromeMat: THREE.MeshStandardMaterial;
    pantsMat: THREE.MeshStandardMaterial;
    shoeMat: THREE.MeshStandardMaterial;
    glassesMat: THREE.MeshStandardMaterial;
    shadowMat: THREE.MeshBasicMaterial;
  }
): BuiltClinician {
  const variantIdx = Math.abs(agent.avatarVariant || 0) % 8;
  const accentMat = new THREE.MeshStandardMaterial({
    color: new THREE.Color(agent.scrubColor || "#0284c7"),
    roughness: 0.55,
    metalness: 0.05,
  });
  const skinMat = new THREE.MeshStandardMaterial({
    color: new THREE.Color(SKIN_TONES[variantIdx]),
    roughness: 0.58,
    metalness: 0.02,
  });
  const hairMat = new THREE.MeshStandardMaterial({
    color: new THREE.Color(HAIR_COLORS[variantIdx]),
    roughness: 0.72,
    metalness: 0.08,
  });

  const group = new THREE.Group();

  // Soft contact shadow disc on the floor
  const shadowDisc = new THREE.Mesh(new THREE.PlaneGeometry(0.95, 0.95), shared.shadowMat);
  shadowDisc.rotation.x = -Math.PI / 2;
  shadowDisc.position.y = 0.008;
  group.add(shadowDisc);

  // Clean Dark Matte Pedestal Base (uncluttered inside glowing floor ring)
  const baseDisc = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.19, 0.035, 18), shared.chairMat);
  baseDisc.position.y = 0.02;
  group.add(baseDisc);

  const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.036, 0.044, 0.22, 12), shared.chairMat);
  stem.position.y = 0.14;
  group.add(stem);

  // Executive Swivel Chair Seat & Lumbar Backrest
  const seatBase = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.22, 0.075, 20), shared.chairMat);
  seatBase.position.set(0, 0.27, 0.02);
  seatBase.scale.set(1.05, 1, 0.96);
  seatBase.castShadow = true;
  group.add(seatBase);

  const seatCushion = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.045, 0.38), shared.chairPadMat);
  seatCushion.position.set(0, 0.305, 0.03);
  group.add(seatCushion);

  // Contoured Backrest + Headrest Bolster
  const backrest = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.48, 0.065), shared.chairMat);
  backrest.position.set(0, 0.56, -0.18);
  backrest.rotation.x = -0.1;
  backrest.castShadow = true;
  group.add(backrest);

  const lumbarPad = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.19, 0.4, 14, 1, false, -0.8, 1.6), shared.chairPadMat);
  lumbarPad.position.set(0, 0.55, -0.14);
  lumbarPad.rotation.x = -0.1;
  group.add(lumbarPad);

  const headrest = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.11, 0.065), shared.chairPadMat);
  headrest.position.set(0, 0.84, -0.21);
  headrest.rotation.x = -0.08;
  group.add(headrest);

  // Armrests with Chrome Supports
  [-1, 1].forEach((side) => {
    const support = new THREE.Mesh(new THREE.BoxGeometry(0.025, 0.14, 0.04), shared.chromeMat);
    support.position.set(side * 0.235, 0.35, -0.02);
    const pad = new THREE.Mesh(new THREE.BoxGeometry(0.055, 0.032, 0.3), shared.chairPadMat);
    pad.position.set(side * 0.235, 0.43, 0.01);
    group.add(support, pad);
  });

  // Seated Legs & Shoes
  const thighGeom = new THREE.CylinderGeometry(0.062, 0.056, 0.3, 12);
  thighGeom.rotateX(Math.PI / 2);
  [-1, 1].forEach((side) => {
    const thigh = new THREE.Mesh(thighGeom, shared.pantsMat);
    thigh.position.set(side * 0.095, 0.35, 0.15);
    const calf = new THREE.Mesh(new THREE.CylinderGeometry(0.052, 0.042, 0.27, 12), shared.pantsMat);
    calf.position.set(side * 0.095, 0.19, 0.28);
    const shoe = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.045, 0.14), shared.shoeMat);
    shoe.position.set(side * 0.095, 0.045, 0.31);
    group.add(thigh, calf, shoe);
  });

  // Animated Upper Body (Torso + Arms + Lapels + Stethoscope)
  const torsoGroup = new THREE.Group();
  torsoGroup.position.set(0, 0.34, 0.0);
  group.add(torsoGroup);

  const wearsScrubsOnly = agent.avatarVariant % 3 === 1;
  const torsoMat = wearsScrubsOnly ? accentMat : shared.coatMat;

  const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.165, 0.185, 0.42, 16), torsoMat);
  torso.position.set(0, 0.22, 0.0);
  torso.scale.set(1.08, 1, 0.78);
  torso.castShadow = true;
  torsoGroup.add(torso);

  // Inner scrub shirt / collar
  const collar = new THREE.Mesh(new THREE.CylinderGeometry(0.085, 0.105, 0.14, 14), accentMat);
  collar.position.set(0, 0.39, 0.025);
  torsoGroup.add(collar);

  // Lab coat lapels when wearing white coat
  if (!wearsScrubsOnly) {
    [-1, 1].forEach((side) => {
      const lapel = new THREE.Mesh(new THREE.BoxGeometry(0.055, 0.22, 0.025), shared.coatMat);
      lapel.position.set(side * 0.068, 0.3, 0.125);
      lapel.rotation.z = side * -0.22;
      torsoGroup.add(lapel);
    });
  }

  // Draped 3D Stethoscope around neck
  if (agent.propType === "stethoscope" || !wearsScrubsOnly) {
    const stethLoop = new THREE.Mesh(
      new THREE.TorusGeometry(0.105, 0.012, 8, 20, Math.PI * 1.35),
      shared.chairMat
    );
    stethLoop.position.set(0, 0.42, 0.02);
    stethLoop.rotation.x = Math.PI / 2 + 0.32;
    stethLoop.rotation.z = -Math.PI * 0.18;
    torsoGroup.add(stethLoop);
  }

  // Arms + Hands
  const upperArmGeom = new THREE.CylinderGeometry(0.048, 0.042, 0.27, 12);
  [-1, 1].forEach((side) => {
    const arm = new THREE.Mesh(upperArmGeom, torsoMat);
    arm.position.set(side * 0.205, 0.24, 0.05);
    arm.rotation.z = side * -0.14;
    arm.rotation.x = -0.4;
    const hand = new THREE.Mesh(new THREE.SphereGeometry(0.036, 10, 10), skinMat);
    hand.position.set(side * 0.185, 0.12, 0.14);
    torsoGroup.add(arm, hand);
  });

  // Tablet or Clipboard prop
  if (agent.propType === "tablet") {
    const tablet = new THREE.Mesh(
      new THREE.BoxGeometry(0.21, 0.014, 0.15),
      new THREE.MeshStandardMaterial({ color: 0x0f172a, emissive: 0x38bdf8, emissiveIntensity: 0.45 })
    );
    tablet.position.set(0, 0.12, 0.22);
    tablet.rotation.x = -0.35;
    torsoGroup.add(tablet);
  } else if (agent.propType === "clipboard") {
    const board = new THREE.Mesh(
      new THREE.BoxGeometry(0.19, 0.012, 0.24),
      new THREE.MeshStandardMaterial({ color: 0x92400e, roughness: 0.7 })
    );
    board.position.set(0.04, 0.13, 0.21);
    board.rotation.x = -0.3;
    const paper = new THREE.Mesh(
      new THREE.BoxGeometry(0.16, 0.006, 0.2),
      new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.8 })
    );
    paper.position.set(0.04, 0.138, 0.21);
    paper.rotation.x = -0.3;
    torsoGroup.add(board, paper);
  }

  // Neck & Head Group (supports subtle head turns)
  const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.058, 0.09, 12), skinMat);
  neck.position.set(0, 0.46, 0.01);
  torsoGroup.add(neck);

  const headGroup = new THREE.Group();
  headGroup.position.set(0, 0.58, 0.02);
  torsoGroup.add(headGroup);

  const head = new THREE.Mesh(new THREE.SphereGeometry(0.138, 20, 18), skinMat);
  head.scale.set(0.95, 1.05, 0.98);
  head.castShadow = true;
  headGroup.add(head);

  // Ears
  [-1, 1].forEach((side) => {
    const ear = new THREE.Mesh(new THREE.SphereGeometry(0.026, 8, 8), skinMat);
    ear.position.set(side * 0.13, 0, -0.01);
    headGroup.add(ear);
  });

  // 4 Varied Hair Styles
  const hairStyle = variantIdx % 4;
  const hairCap = new THREE.Mesh(
    new THREE.SphereGeometry(0.145, 18, 14, 0, Math.PI * 2, 0, Math.PI * 0.58),
    hairMat
  );
  hairCap.position.set(0, 0.02, -0.01);
  hairCap.rotation.x = -0.24;
  headGroup.add(hairCap);

  if (hairStyle === 1) {
    // Bun at back of head
    const bun = new THREE.Mesh(new THREE.SphereGeometry(0.062, 12, 12), hairMat);
    bun.position.set(0, 0.03, -0.155);
    headGroup.add(bun);
  } else if (hairStyle === 2) {
    // Shoulder-length bob
    const backHair = new THREE.Mesh(new THREE.CylinderGeometry(0.135, 0.145, 0.16, 14, 1, false, Math.PI * 0.4, Math.PI * 1.2), hairMat);
    backHair.position.set(0, -0.05, -0.015);
    headGroup.add(backHair);
  }

  // Glasses when hasGlasses is true
  if (agent.hasGlasses) {
    [-1, 1].forEach((side) => {
      const rim = new THREE.Mesh(new THREE.TorusGeometry(0.032, 0.005, 6, 16), shared.glassesMat);
      rim.position.set(side * 0.044, 0.015, 0.128);
      headGroup.add(rim);
    });
    const bridge = new THREE.Mesh(new THREE.BoxGeometry(0.028, 0.006, 0.006), shared.glassesMat);
    bridge.position.set(0, 0.018, 0.13);
    headGroup.add(bridge);
  }

  return { group, torsoGroup, headGroup };
}
