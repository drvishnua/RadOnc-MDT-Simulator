import type { Agent } from "../types.js";

export function SpecialistsTab({
  agents,
  filteredAgents,
  agentFilter,
  categories,
  onFilterChange
}: {
  agents: Agent[];
  filteredAgents: Agent[];
  agentFilter: string;
  categories: string[];
  onFilterChange: (nextFilter: string) => void;
}) {
  return (
    <section className="panel agents-panel tab-view-container" style={{ width: "100%", maxWidth: "100%" }}>
      <div className="panel-heading">
        <div>
          <p className="eyebrow">02 / MDT PERSPECTIVES</p>
          <h2>Agent directory</h2>
        </div>
        <span className="count-chip">{agents.length || 49} ROLES</span>
      </div>
      <p className="panel-intro">
        Every role participates across all 4 discussion rounds. Critical &amp; contrarian roles offer rigorous adversarial cross-examination.
      </p>

      <label className="filter-label">
        Filter by perspective
        <select value={agentFilter} onChange={(event) => onFilterChange(event.target.value)}>
          {categories.map((category) => <option key={category}>{category}</option>)}
        </select>
      </label>

      <div className="agent-list">
        {filteredAgents.map((agent) => {
          const isContrarian = ["RO-10", "MO-09", "SO-09", "SG-09"].includes(agent.agent_id);
          return (
            <article className={`agent-item ${isContrarian ? "agent-item-contrarian" : ""}`} key={agent.agent_id}>
              <div className="agent-header-row">
                <span className={`agent-id ${isContrarian ? "agent-id-contrarian" : ""}`}>{agent.agent_id}</span>
                {isContrarian && <span className="contrarian-badge">CRITICAL / CONTRARIAN</span>}
                {agent.risk_appetite && (
                  <span className={`risk-badge risk-${agent.risk_appetite.toLowerCase()}`}>
                    {agent.risk_appetite.toUpperCase()} RISK
                  </span>
                )}
              </div>
              <div className="agent-copy">
                <strong>{agent.name}</strong>
                <p>{agent.mandate}</p>
                {agent.clinical_philosophy && (
                  <p className="agent-philosophy">
                    <em>Philosophy:</em> {agent.clinical_philosophy}
                  </p>
                )}
              </div>
            </article>
          );
        })}
        {agents.length === 0 && (
          <p className="empty-state">The agent catalogue will appear when the backend API is running.</p>
        )}
      </div>
      <p className="directory-footnote">Showing {filteredAgents.length} of {agents.length} configured perspectives.</p>
    </section>
  );
}
