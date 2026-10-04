import { kindOf } from '../kinds';

export default function SourceViewer({ chunk, onClose }) {
  if (!chunk) return null;
  const k = kindOf(chunk.source_type);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>
            <span
              className="cite-chip"
              style={{ background: k.bg, color: k.color, marginRight: 8 }}
            >
              {k.icon} {k.label}
            </span>
            {chunk.source_file}
          </h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          {chunk.text || chunk.text_preview || '(no preview available)'}
        </div>
      </div>
    </div>
  );
}
