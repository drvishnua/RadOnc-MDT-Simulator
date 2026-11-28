import React from "react";

const SKIN_TONES = ["#F5CBA7", "#E0AC69", "#C68642", "#8D5524", "#FAD7A0", "#D5A078", "#A5694F", "#F1C27D"];
const HAIR_COLORS = ["#1E293B", "#4A3728", "#0F172A", "#6D4C3D", "#94A3B8", "#3B2F2F", "#2C222B", "#7C4D3A"];

export interface DoctorAvatarProps {
  variant?: number;
  scrubColor?: string;
  hasGlasses?: boolean;
  propType?: "tablet" | "clipboard" | "stethoscope" | "none";
  size?: number;
  seated?: boolean;
  className?: string;
}

export const DoctorAvatar: React.FC<DoctorAvatarProps> = ({
  variant = 0,
  scrubColor = "#38BDF8",
  hasGlasses = false,
  propType = "stethoscope",
  size = 56,
  seated = false,
  className = "",
}) => {
  const idx = Math.abs(variant) % 8;
  const skin = SKIN_TONES[idx];
  const hair = HAIR_COLORS[idx];
  const longHair = idx % 2 === 1;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 80 84"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      {/* Subtle 2.5D chair backrest when seated */}
      {seated && (
        <g>
          <rect
            x="14"
            y="30"
            width="52"
            height="42"
            rx="12"
            className="fill-slate-700/90 stroke-slate-500/50 dark:fill-slate-800 dark:stroke-sky-400/25"
            strokeWidth="1.5"
          />
          <rect
            x="20"
            y="34"
            width="40"
            height="30"
            rx="8"
            className="fill-slate-600/40 dark:fill-slate-900/60"
          />
        </g>
      )}

      {/* White Clinical Coat & Scrubs */}
      <path
        d="M17 78 C17 56, 26 48, 40 48 C54 48, 63 56, 63 78 Z"
        fill="#F8FAFC"
        stroke="#CBD5E1"
        strokeWidth="1.5"
      />
      {/* Scrub V-neck */}
      <path d="M31 49 L40 66 L49 49 Z" fill={scrubColor} opacity="0.92" />
      {/* Lab coat lapels */}
      <path d="M30 49 L35 66 L26 64 Z" fill="#E2E8F0" />
      <path d="M50 49 L45 66 L54 64 Z" fill="#E2E8F0" />

      {/* Stethoscope */}
      {(propType === "stethoscope" || seated) && (
        <path
          d="M30 49 C29 58, 34 62, 40 62 C46 62, 51 58, 50 49"
          stroke="#475569"
          strokeWidth="2.2"
          strokeLinecap="round"
        />
      )}

      {/* Neck & Head */}
      <rect x="35" y="40" width="10" height="10" rx="4" fill={skin} />
      {longHair && (
        <path d="M23 26 C23 13, 57 13, 57 26 L58 43 L22 43 Z" fill={hair} />
      )}
      <ellipse cx="40" cy="28" rx="13.5" ry="15" fill={skin} />

      {/* Hair crown */}
      <path
        d={
          longHair
            ? "M25 27 C25 14, 55 14, 55 27 C51 20, 45 19, 40 20 C35 19, 29 20, 25 27 Z"
            : "M26 25 C26 12, 54 12, 54 25 C50 19, 30 19, 26 25 Z"
        }
        fill={hair}
      />

      {/* Eyes & Smile */}
      <circle cx="34.5" cy="29" r="1.6" fill="#0F172A" />
      <circle cx="45.5" cy="29" r="1.6" fill="#0F172A" />
      <path
        d="M35.5 35.5 Q40 38.5 44.5 35.5"
        stroke="#7C2D12"
        strokeWidth="1.6"
        strokeLinecap="round"
        fill="none"
      />

      {/* Glasses */}
      {hasGlasses && (
        <g stroke="#1E293B" strokeWidth="1.5" fill="rgba(56, 189, 248, 0.14)">
          <rect x="29.5" y="25.5" width="9" height="6.5" rx="2" />
          <rect x="41.5" y="25.5" width="9" height="6.5" rx="2" />
          <line x1="38.5" y1="28.5" x2="41.5" y2="28.5" />
        </g>
      )}

      {/* Tablet or Clipboard prop */}
      {propType === "tablet" && (
        <g>
          <rect
            x="48"
            y="58"
            width="14"
            height="17"
            rx="2.5"
            fill="#0F172A"
            stroke="#38BDF8"
            strokeWidth="1.2"
          />
          <rect x="50.5" y="61" width="9" height="10" rx="1" fill="#38BDF8" opacity="0.45" />
        </g>
      )}
      {propType === "clipboard" && (
        <g>
          <rect x="18" y="57" width="13" height="17" rx="2" fill="#94A3B8" stroke="#475569" strokeWidth="1.2" />
          <rect x="20" y="60" width="9" height="11" rx="1" fill="#FFFFFF" />
          <line x1="22" y1="63" x2="27" y2="63" stroke="#64748B" strokeWidth="1" />
          <line x1="22" y1="66" x2="27" y2="66" stroke="#64748B" strokeWidth="1" />
        </g>
      )}
    </svg>
  );
};

export interface IntakeHostIllustrationProps {
  mode: "intake" | "audit";
  listening?: boolean;
  className?: string;
}

export const IntakeHostIllustration: React.FC<IntakeHostIllustrationProps> = ({
  mode,
  listening = false,
  className = "",
}) => {
  const isAudit = mode === "audit";

  return (
    <div className={`relative flex items-center justify-center select-none ${className}`}>
      {/* Ambient clinical glow */}
      <div
        className={`pointer-events-none absolute inset-6 rounded-full blur-3xl transition-all duration-500 ${
          listening
            ? "bg-emerald-400/25 dark:bg-emerald-400/20 scale-110"
            : isAudit
              ? "bg-sky-400/25 dark:bg-sky-400/20"
              : "bg-cyan-400/20 dark:bg-sky-500/15"
        }`}
      />

      <svg viewBox="0 0 260 310" className="relative z-10 h-full max-h-[340px] w-auto drop-shadow-xl" fill="none">
        {/* Audit vertical scan glow */}
        {isAudit && (
          <g opacity="0.85">
            <rect
              x="36"
              y="92"
              width="188"
              height="160"
              rx="16"
              stroke="url(#scanFrame)"
              strokeWidth="1.5"
              fill="url(#scanFill)"
            />
            <rect x="42" y="130" width="176" height="6" rx="3" fill="#38BDF8" className="audit-scan-beam" opacity="0.55" />
          </g>
        )}

        {/* Coat Torso */}
        <path
          d="M48 302 C48 214, 78 182, 130 182 C182 182, 212 214, 212 302 Z"
          fill="#F8FAFC"
          stroke="#CBD5E1"
          strokeWidth="2.5"
        />
        {/* Scrubs */}
        <path d="M102 184 L130 250 L158 184 Z" fill="#0EA5E9" />
        {/* Lapels */}
        <path d="M98 184 L118 256 L84 242 Z" fill="#E2E8F0" />
        <path d="M162 184 L142 256 L176 242 Z" fill="#E2E8F0" />
        {/* Pocket & Pen */}
        <rect x="155" y="232" width="26" height="30" rx="4" fill="#F1F5F9" stroke="#CBD5E1" strokeWidth="1.5" />
        <line x1="164" y1="222" x2="164" y2="238" stroke="#1E293B" strokeWidth="3" strokeLinecap="round" />

        {/* Stethoscope */}
        <path
          d="M94 185 C90 218, 108 232, 130 232 C152 232, 170 218, 166 185"
          stroke="#334155"
          strokeWidth="5"
          strokeLinecap="round"
        />
        <circle cx="130" cy="234" r="8" fill="#64748B" stroke="#0F172A" strokeWidth="2" />

        {/* Neck & Head */}
        <rect x="114" y="152" width="32" height="34" rx="12" fill="#E9B892" />
        <ellipse cx="130" cy="108" rx="44" ry="50" fill="#F2C6A0" />

        {/* Hair */}
        <path
          d="M84 100 C82 54, 176 48, 176 98 C162 72, 146 66, 128 68 C110 70, 96 76, 84 100 Z"
          fill="#2D201A"
        />
        {/* Ears */}
        <ellipse cx="85" cy="112" rx="6" ry="10" fill="#E5B289" />
        <ellipse cx="175" cy="112" rx="6" ry="10" fill="#E5B289" />

        {/* Eyebrows & Eyes */}
        <path d="M101 94 Q112 88 122 93" stroke="#2D201A" strokeWidth="3" strokeLinecap="round" />
        <path d="M138 93 Q148 88 159 94" stroke="#2D201A" strokeWidth="3" strokeLinecap="round" />
        <circle cx="112" cy="108" r="4.5" fill="#0F172A" />
        <circle cx="148" cy="108" r={isAudit ? "6.2" : "4.5"} fill="#0F172A" />
        <circle cx="113.5" cy="106.5" r="1.4" fill="#FFFFFF" />
        <circle cx="149.8" cy="106.2" r="1.6" fill="#FFFFFF" />

        {/* Smile */}
        <path
          d="M114 132 Q130 144 146 132"
          stroke="#9A3412"
          strokeWidth="3.2"
          strokeLinecap="round"
          fill="none"
        />

        {/* Glasses */}
        <g stroke="#1E293B" strokeWidth="3" fill="rgba(56, 189, 248, 0.12)">
          <rect x="96" y="97" width="29" height="21" rx="6" />
          <rect x="135" y="97" width="29" height="21" rx="6" />
          <line x1="125" y1="107" x2="135" y2="107" />
        </g>

        {/* Audit Mode Magnifying Glass held to eye */}
        {isAudit && (
          <g>
            <circle
              cx="150"
              cy="108"
              r="26"
              fill="rgba(56, 189, 248, 0.2)"
              stroke="#64748B"
              strokeWidth="6"
            />
            <circle cx="150" cy="108" r="22" stroke="#38BDF8" strokeWidth="1.5" opacity="0.8" />
            <line
              x1="168"
              y1="128"
              x2="195"
              y2="162"
              stroke="#334155"
              strokeWidth="9"
              strokeLinecap="round"
            />
            {/* Hand gripping lens */}
            <circle cx="193" cy="162" r="12" fill="#F2C6A0" stroke="#D9A173" strokeWidth="1.5" />
          </g>
        )}

        <defs>
          <linearGradient id="scanFrame" x1="36" y1="92" x2="224" y2="252" gradientUnits="userSpaceOnUse">
            <stop stopColor="#38BDF8" stopOpacity="0.65" />
            <stop offset="1" stopColor="#10B981" stopOpacity="0.15" />
          </linearGradient>
          <linearGradient id="scanFill" x1="130" y1="92" x2="130" y2="252" gradientUnits="userSpaceOnUse">
            <stop stopColor="#38BDF8" stopOpacity="0.12" />
            <stop offset="1" stopColor="#38BDF8" stopOpacity="0" />
          </linearGradient>
        </defs>
      </svg>
    </div>
  );
};

export default DoctorAvatar;
