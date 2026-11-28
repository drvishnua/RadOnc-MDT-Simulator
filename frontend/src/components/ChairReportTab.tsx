import { LANDMARK_TRIALS, getSiteConstraints } from "../clinicalEvidence.js";
import type { FinalMDTReport } from "../types.js";

export function ChairReportTab({
  finalReport,
  primarySite,
  onGoToSimulation,
  onOpenEvidenceDrawer
}: {
  finalReport: FinalMDTReport | null;
  primarySite: string;
  onGoToSimulation: () => void;
  onOpenEvidenceDrawer: () => void;
}) {
  return (
    <section className="panel tab-view-container" style={{ width: "100%", maxWidth: "100%" }}>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">03 / FINAL REPORT</p>
          <h2>MDT Chair Deliberation &amp; Consensus Synthesis</h2>
        </div>
        <span className="panel-index">CHAIR SYNTHESIS</span>
      </div>
      {!finalReport ? (
        <div className="result-card" style={{ padding: "40px", textAlign: "center", marginTop: "16px" }}>
          <span style={{ fontSize: "40px", display: "block", marginBottom: "16px" }}>📋</span>
          <h3 style={{ fontSize: "18px", color: "#f8fafc" }}>No Chair Report Available Yet</h3>
          <p style={{ color: "#94a3b8", maxWidth: "520px", margin: "12px auto", lineHeight: "1.5" }}>
            The Chair Synthesis is formulated after Rounds 1–4 are executed. Run a simulation from the MDT Simulation tab to generate the final consensus report.
          </p>
          <button className="button button-primary" type="button" onClick={onGoToSimulation}>
            Go to MDT Simulation (Step 2) →
          </button>
        </div>
      ) : (
        <div className="final-mdt-report" style={{ marginTop: "20px" }}>
          <div style={{ display: "flex", gap: "10px", marginBottom: "16px", flexWrap: "wrap" }}>
            <button
              type="button"
              className="button button-primary"
              onClick={() => window.print()}
            >
              🖨️ Export / Print MDT Summary
            </button>
            <button
              type="button"
              className="button"
              onClick={onOpenEvidenceDrawer}
            >
              📚 Landmark Trials &amp; Evidence Library ({LANDMARK_TRIALS.length})
            </button>
          </div>

          <div className="assessment-conclusion">
            <p className="eyebrow">ROUND 4 · CHAIR SYNTHESIS</p>
            <h3 style={{ fontSize: "20px", color: "#38bdf8", marginBottom: "12px" }}>{finalReport.report_title}</h3>
            <span className={`consensus-badge-large ${finalReport.consensus_status}`}>
              {finalReport.consensus_status.replaceAll("_", " ")}
            </span>
            <div style={{ marginTop: "16px" }}>
              <strong style={{ display: "block", fontSize: "14px", color: "#f8fafc", marginBottom: "6px" }}>Primary Chair Conclusion:</strong>
              <p style={{ fontSize: "15px", lineHeight: "1.6", color: "#e2e8f0" }}>{finalReport.chair_conclusion}</p>
            </div>
            <div style={{ marginTop: "16px" }}>
              <strong style={{ display: "block", fontSize: "14px", color: "#f8fafc", marginBottom: "6px" }}>Overall Educational Synthesis:</strong>
              <p style={{ lineHeight: "1.6", color: "#cbd5e1" }}>{finalReport.overall_educational_synthesis}</p>
            </div>
          </div>

          <div className="dosimetry-card">
            <div className="dosimetry-title">
              <span>📐</span>
              <strong>QUANTEC / PENTEC Organs-At-Risk (OAR) Dosimetric Tolerances</strong>
              <span className="count-chip" style={{ marginLeft: "auto", fontSize: "10px" }}>{(primarySite || "Site").toUpperCase()}</span>
            </div>
            <p className="dosimetry-subtitle">
              Authoritative normal tissue dose-volume limits for treatment planning and peer review safety.
            </p>
            <table className="dosimetry-table">
              <thead>
                <tr>
                  <th>Organ</th>
                  <th>Dose-Volume Metric</th>
                  <th>Constraint Limit</th>
                  <th>Endpoint / Clinical Complication</th>
                  <th>Risk Tier</th>
                </tr>
              </thead>
              <tbody>
                {getSiteConstraints(primarySite || "").map((c) => (
                  <tr key={c.id}>
                    <td><strong>{c.organ}</strong></td>
                    <td className="dosimetry-metric">{c.metric}</td>
                    <td className="dosimetry-limit">{c.operator} {c.limitValue} {c.unit}</td>
                    <td>{c.endpoint}</td>
                    <td><span className="step-badge ready">{c.riskLevel.replaceAll("_", " ")}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {finalReport.consensus_points.length > 0 && (
            <div className="report-section" style={{ marginTop: "16px" }}>
              <strong style={{ color: "#4ade80" }}>✓ Consensus Points</strong>
              <ul>{finalReport.consensus_points.map((value, index) => <li key={index}>{value}</li>)}</ul>
            </div>
          )}
          {finalReport.unresolved_disagreements.length > 0 && (
            <div className="report-section" style={{ marginTop: "16px" }}>
              <strong style={{ color: "#fb7185" }}>⚠ Unresolved Disagreements</strong>
              <ul>{finalReport.unresolved_disagreements.map((value, index) => <li key={index}>{value}</li>)}</ul>
            </div>
          )}
          {finalReport.minority_and_dissenting_views.length > 0 && (
            <div className="report-section" style={{ marginTop: "16px" }}>
              <strong style={{ color: "#facc15" }}>Minority &amp; Dissenting Views</strong>
              <ul>{finalReport.minority_and_dissenting_views.map((value, index) => <li key={index}>{value}</li>)}</ul>
            </div>
          )}
          {finalReport.major_uncertainties.length > 0 && (
            <div className="report-section" style={{ marginTop: "16px" }}>
              <strong style={{ color: "#38bdf8" }}>Major Clinical Uncertainties</strong>
              <ul>{finalReport.major_uncertainties.map((value, index) => <li key={index}>{value}</li>)}</ul>
            </div>
          )}
          {finalReport.missing_information_before_real_world_review.length > 0 && (
            <div className="report-section" style={{ marginTop: "16px" }}>
              <strong style={{ color: "#94a3b8" }}>Required Diagnostics Before Treatment</strong>
              <ul>{finalReport.missing_information_before_real_world_review.map((value, index) => <li key={index}>{value}</li>)}</ul>
            </div>
          )}
          <div className="report-section" style={{ marginTop: "16px" }}>
            <strong>Chair Reflection</strong>
            <p style={{ fontStyle: "italic", lineHeight: "1.6", color: "#94a3b8" }}>"{finalReport.chair_reflection}"</p>
          </div>
          <p className="result-footnote" style={{ marginTop: "16px" }}>
            Educational simulation only. This report is an educational synthesis and does not constitute a clinical recommendation.
          </p>
        </div>
      )}
    </section>
  );
}
