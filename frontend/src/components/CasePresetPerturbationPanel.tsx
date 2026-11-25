import { PRESET_CASES } from "../presetCases.js";

export interface CasePresetPerturbationPanelProps {
  selectedPresetId: string;
  onSelectPreset: (id: string) => void;
  onLoadPreset: (id: string) => void;
}

export function CasePresetPerturbationPanel({
  selectedPresetId,
  onSelectPreset,
  onLoadPreset,
}: CasePresetPerturbationPanelProps) {
  return (
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
  );
}
