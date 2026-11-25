import { LANDMARK_TRIALS } from "../clinicalEvidence.js";
import type { LandmarkTrial } from "../clinicalEvidence.js";

export function EvidenceDrawerModal({
  inspectingTrial,
  onSelectTrial,
  onClose
}: {
  inspectingTrial: LandmarkTrial | null;
  onSelectTrial: (trial: LandmarkTrial | null) => void;
  onClose: () => void;
}) {
  return (
    <div className="evidence-drawer-overlay" onClick={onClose}>
      <div className="evidence-drawer" onClick={(e) => e.stopPropagation()}>
        <div className="evidence-drawer-header">
          <div className="evidence-drawer-title">
            <span>📚</span>
            <strong>Landmark Trials &amp; Evidence Library</strong>
          </div>
          <button
            type="button"
            className="button"
            style={{ padding: "4px 10px" }}
            onClick={onClose}
          >
            ✕ Close
          </button>
        </div>
        <div className="evidence-drawer-body">
          {inspectingTrial ? (
            <div>
              <button
                type="button"
                className="button"
                style={{ marginBottom: "14px", fontSize: "11px" }}
                onClick={() => onSelectTrial(null)}
              >
                ← Back to All Trials
              </button>
              <div className="trial-card-full">
                <div className="trial-card-title">{inspectingTrial.name}</div>
                <div className="trial-citation-text">{inspectingTrial.citation}</div>
                <div className="trial-field-group">
                  <div className="trial-field-label">Target Population</div>
                  <div className="trial-field-value">{inspectingTrial.population}</div>
                </div>
                <div className="trial-field-group">
                  <div className="trial-field-label">Primary Endpoint</div>
                  <div className="trial-field-value">{inspectingTrial.primaryEndpoint}</div>
                </div>
                <div className="trial-field-group">
                  <div className="trial-field-label">Clinical Outcomes</div>
                  <div className="trial-field-value">{inspectingTrial.outcome}</div>
                </div>
                <div className="trial-takeaway-box">
                  <strong>Radiation Oncology Key Takeaway:</strong>
                  <p style={{ marginTop: "4px", lineHeight: "1.5" }}>{inspectingTrial.radOncTakeaway}</p>
                </div>
                <div style={{ marginTop: "14px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span className="step-badge ready">{inspectingTrial.guidelineLevel}</span>
                  <span style={{ fontSize: "11px", color: "#94a3b8" }}>PMID: {inspectingTrial.pmid}</span>
                </div>
              </div>
            </div>
          ) : (
            <div>
              <p style={{ fontSize: "12px", color: "#94a3b8", marginBottom: "16px", lineHeight: "1.5" }}>
                Key landmark trials referenced across the 4 discussion rounds. Click any trial to inspect endpoints, hazard ratios, and radiation oncology takeaways:
              </p>
              {LANDMARK_TRIALS.map((trial) => (
                <div
                  key={trial.id}
                  className="trial-card-full"
                  style={{ cursor: "pointer" }}
                  onClick={() => onSelectTrial(trial)}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "4px" }}>
                    <div className="trial-card-title">{trial.name}</div>
                    <span className="count-chip" style={{ fontSize: "10px" }}>{trial.primarySite}</span>
                  </div>
                  <div className="trial-citation-text">{trial.citation}</div>
                  <p style={{ fontSize: "12px", color: "#cbd5e1", lineHeight: "1.4" }}>{trial.radOncTakeaway}</p>
                  <div style={{ marginTop: "8px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span className="step-badge ready" style={{ fontSize: "10px" }}>{trial.guidelineLevel}</span>
                    <span style={{ fontSize: "11px", color: "#38bdf8" }}>Inspect trial details →</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
