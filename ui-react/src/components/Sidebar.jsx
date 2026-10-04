const MODES = [
  { id: 'general',    icon: '🔍', label: 'General QA',       desc: 'Ask anything about your QA suite' },
  { id: 'selenium',   icon: '⌨️', label: 'Selenium',          desc: 'Framework code & test patterns' },
  { id: 'playwright', icon: '🎭', label: 'Playwright',        desc: 'Playwright tests & selectors' },
  { id: 'jira',       icon: '🐞', label: 'Jira Tickets',      desc: 'Bugs, tasks, and user stories' },
  { id: 'ci',         icon: '🧯', label: 'CI / Jenkins',      desc: 'Build logs & pipeline failures' },
  { id: 'docs',       icon: '📄', label: 'Docs & PRDs',       desc: 'Requirements and specifications' },
];

export default function Sidebar({ mode, setMode, sources, enabledSources, toggleSource, onIngest, ingesting }) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1>🧪 QABuddy.ai</h1>
        <p>Hybrid RAG · Selenium · Playwright · Jira</p>
      </div>

      <div className="sidebar-section">
        <h3>Mode</h3>
        {MODES.map((m) => (
          <button
            key={m.id}
            className={`mode-btn${mode === m.id ? ' active' : ''}`}
            onClick={() => setMode(m.id)}
            title={m.desc}
          >
            <span>{m.icon}</span>
            <span>{m.label}</span>
          </button>
        ))}
      </div>

      <div className="sidebar-section" style={{ flex: 1, overflowY: 'auto' }}>
        <h3>Knowledge Sources</h3>
        {sources.map((s) => (
          <label key={s.id} className="source-toggle">
            <input
              type="checkbox"
              checked={enabledSources.has(s.id)}
              onChange={() => toggleSource(s.id)}
            />
            {s.icon} {s.label}
          </label>
        ))}
      </div>

      <div className="sidebar-footer">
        <button className="ingest-btn" onClick={onIngest} disabled={ingesting}>
          {ingesting ? '⏳ Ingesting…' : '🔄 Re-ingest data'}
        </button>
      </div>
    </div>
  );
}
