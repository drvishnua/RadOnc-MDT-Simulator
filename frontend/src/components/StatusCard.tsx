export function StatusCard({
  label,
  value,
  detail,
  state
}: {
  label: string;
  value: string;
  detail: string;
  state: "good" | "bad" | "neutral";
}) {
  return (
    <article className="status-card">
      <div className="status-card-top">
        <span>{label}</span>
        <span className={"status-light " + state} />
      </div>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}
