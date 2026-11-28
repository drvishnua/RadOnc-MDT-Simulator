import type { PendingIntake } from "../types.js";

export interface PreMdtIntakeReviewCardProps {
  pendingIntake: PendingIntake;
  patientBusy: boolean;
  onDeclineQuestion: (domain: string) => void;
  onReturnToForm: () => void;
  onAcceptAndPromote: () => void;
}

export function PreMdtIntakeReviewCard({
  pendingIntake,
  patientBusy,
  onDeclineQuestion,
  onReturnToForm,
  onAcceptAndPromote,
}: PreMdtIntakeReviewCardProps) {
  return (
    <div className="result-card intake-review-card" aria-label="Pre-MDT intake review">
      <strong>Pre-MDT intake review</strong>
      <p>
        Review the missing information below. You can return to the case form, add documented
        details, validate again and start a revised intake. Accepting with gaps preserves them as
        unknown; it does not make the case clinically complete.
      </p>
      {pendingIntake.screening ? (
        <>
          {pendingIntake.screening.questions.length > 0 ? (
            <div className="intake-question-list">
              {pendingIntake.screening.questions.map((question) => {
                const isConflict = question.domain === "clinical_conflicts";
                const missingFields = pendingIntake.screening!.gaps
                  .filter((gap) => gap.domain === question.domain)
                  .map((gap) => gap.field_id)
                  .join(", ");
                return (
                  <div className="intake-question" key={`${question.domain}:${question.field_id ?? ""}`}>
                    <strong>
                      {question.priority === "high" ? "[High priority] " : ""}
                      {question.question}
                    </strong>
                    <p>
                      {isConflict
                        ? `Conflicting field: ${question.field_id ?? "Review required"}`
                        : `Missing fields: ${missingFields || "Review required"}`}
                    </p>
                    {!isConflict && (
                      <button
                        className="button button-quiet"
                        type="button"
                        onClick={() => onDeclineQuestion(question.domain)}
                        disabled={patientBusy}
                      >
                        I cannot provide this information
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <p>No outstanding screening questions remain in the listed domains.</p>
          )}
          {pendingIntake.screening.gaps.length > 0 && (
            <p className="result-footnote">
              Outstanding gaps:{" "}
              {pendingIntake.screening.gaps
                .map((gap) => gap.field_id + (gap.status === "DECLINED" ? " (declined)" : ""))
                .join(", ")}
              .
            </p>
          )}
          <p className="result-footnote">{pendingIntake.screening.disclaimer}</p>
        </>
      ) : (
        <p>Restoring the saved intake review…</p>
      )}
      <div className="batch-actions">
        <button
          className="button button-secondary"
          type="button"
          onClick={onReturnToForm}
          disabled={patientBusy}
        >
          Return to case form
        </button>
        <button
          className="button button-primary"
          type="button"
          onClick={onAcceptAndPromote}
          disabled={patientBusy || !pendingIntake.screening}
        >
          {patientBusy
            ? "Saving…"
            : pendingIntake.screening?.gaps.length
            ? "Accept with gaps and save"
            : "Accept intake and save"}
        </button>
      </div>
    </div>
  );
}
