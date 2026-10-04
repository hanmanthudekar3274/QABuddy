import Answer from './Answer';
import { kindOf } from '../kinds';

export default function Message({ msg, onCiteClick }) {
  if (msg.role === 'user') {
    return <div className="msg-q">{msg.content}</div>;
  }

  return (
    <div className="msg-a">
      {msg.thinking ? (
        <span className="msg-a-thinking">{msg.thinking}</span>
      ) : (
        <Answer text={msg.content} />
      )}
      {msg.citations?.length > 0 && (
        <div className="citations">
          {msg.citations.map((c, i) => {
            const k = kindOf(c.source_type);
            return (
              <button
                key={i}
                className="cite-chip"
                style={{ background: k.bg, color: k.color }}
                onClick={() => onCiteClick?.(c)}
                title={c.source_file}
              >
                {k.icon} {k.label}
              </button>
            );
          })}
        </div>
      )}
      {msg.trace?.length > 0 && <Trace steps={msg.trace} />}
    </div>
  );
}

function Trace({ steps }) {
  return (
    <div className="trace">
      <div className="trace-steps">
        {steps.map((s, i) => (
          <div key={i} className="trace-step">
            <span className="step-dot" />
            {s}
          </div>
        ))}
      </div>
    </div>
  );
}
