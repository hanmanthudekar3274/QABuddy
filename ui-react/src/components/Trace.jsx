import { useState } from 'react';

export default function Trace({ steps = [] }) {
  const [open, setOpen] = useState(false);
  if (!steps.length) return null;

  return (
    <div className="trace">
      <button className="trace-toggle" onClick={() => setOpen(!open)}>
        {open ? '▾' : '▸'} Pipeline trace ({steps.length} steps)
      </button>
      {open && (
        <div className="trace-steps">
          {steps.map((s, i) => (
            <div key={i} className="trace-step">
              <span className="step-dot" />
              {s}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
