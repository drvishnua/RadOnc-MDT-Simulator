import { PRESET_CASES } from "../presetCases.js";
import { CLINICAL_PERTURBATIONS } from "../clinicalPerturbations.js";

export interface CasePresetPerturbationPanelProps {
  selectedPresetId: string;
  onSelectPreset: (id: string) => void;
  onLoadPreset: (id: string) => void;
  activePerturbationId: string | null;
  onApplyPerturbation: (id: string) => void;
  onResetPerturbations: () => void;
}

export function CasePresetPerturbationPanel({
  selectedPresetId,
  onSelectPreset,
  onLoadPreset,
  activePerturbationId,
  onApplyPerturbation,
  onResetPerturbations,
}: CasePresetPerturbationPanelProps) {
  return (
    <>
      <div className="preset-card">
        <div className="preset-header">
          <span className="preset-icon">💡</span>
          <div>
            <strong>Quick Start: Load an Educational Case Preset</strong>
            <p>
              Select from 8 realistic multi-site training cases (Pediatric, AYA, Cervix, Breast,
              Oropharynx, Rectum, Bladder, Lung SBRT) to test the MDT immediately with one click.
            </p>
          </div>
        </div>
        <div className="preset-controls">
          <select
            value={selectedPresetId}
            onChange={(e) => {
              onSelectPreset(e.target.value);
              if (e.target.value) onLoadPreset(e.target.value);
            }}
            className="preset-select"
          >
            <option value="">-- Choose a Pre-Configured Clinical Case --</option>
            {PRESET_CASES.map((preset) => (
              <option key={preset.id} value={preset.id}>
                {preset.badge}: {preset.name}
              </option>
            ))}
          </select>
          <button
            type="button"
            className="button button-primary"
            disabled={!selectedPresetId}
            onClick={() => onLoadPreset(selectedPresetId)}
          >
            Load Case into Form
          </button>
        </div>
        {selectedPresetId && (
          <p className="preset-desc">
            {PRESET_CASES.find((p) => p.id === selectedPresetId)?.description}
          </p>
        )}
      </div>

      <div className="perturbation-card">
        <div className="perturbation-header">
          <div className="perturbation-title">
            <span>🧪</span>
            <strong>What-If? Clinical Perturbation Lab</strong>
            <span style={{ fontSize: "11px", color: "#94a3b8", fontWeight: "normal" }}>
              (Simulate how critical clinical shifts swing the MDT consensus)
            </span>
          </div>
          {activePerturbationId && (
            <button
              type="button"
              className="button"
              style={{ fontSize: "11px", padding: "3px 8px" }}
              onClick={onResetPerturbations}
            >
              ↺ Reset to Baseline Case
            </button>
          )}
        </div>
        <div className="perturbation-grid">
          {CLINICAL_PERTURBATIONS.map((p) => {
            const isActive = activePerturbationId === p.id;
            return (
              <button
                key={p.id}
                type="button"
                className={`perturbation-btn ${isActive ? "active" : ""}`}
                onClick={() => onApplyPerturbation(p.id)}
                title={p.description}
              >
                <span>
                  {p.icon} <strong>{p.label}</strong>
                </span>
                <span style={{ fontSize: "11px", opacity: 0.85 }}>{p.description}</span>
              </button>
            );
          })}
        </div>
        {activePerturbationId && (
          <div className="perturbation-active-banner">
            <span>
              ⚠️ <strong>Perturbation Active:</strong> Case data modified. Re-run{" "}
              <strong>"Validate case draft"</strong> below to screen and initiate simulation!
            </span>
          </div>
        )}
      </div>
    </>
  );
}
