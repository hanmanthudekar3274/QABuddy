import { useState, useEffect, useRef, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import Message from './components/Message';
import SourceViewer from './components/SourceViewer';
import { api } from './client';
import './styles.css';

const EXAMPLES = [
  'How do I wait for an element in Playwright?',
  'What Selenium tests cover the login flow?',
  'Show open bugs from the last sprint',
  'Why did the CI pipeline fail yesterday?',
  'What does the test plan for checkout say?',
  'How is the BM25 sparse search configured?',
];

export default function App() {
  const [health, setHealth] = useState('checking');
  const [sources, setSources] = useState([]);
  const [enabledSources, setEnabledSources] = useState(new Set());
  const [mode, setMode] = useState('general');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [viewChunk, setViewChunk] = useState(null);

  const threadRef = useRef(null);
  const textareaRef = useRef(null);
  const abortRef = useRef(null);

  // Fetch health + sources on mount
  useEffect(() => {
    api.health().then((h) => setHealth(h.status === 'ok' ? 'ok' : 'bad'));
    api.sources().then((s) => {
      setSources(s);
      setEnabledSources(new Set(s.map((x) => x.id)));
    });
  }, []);

  // Scroll thread to bottom when messages change
  useEffect(() => {
    if (threadRef.current) {
      threadRef.current.scrollTop = threadRef.current.scrollHeight;
    }
  }, [messages]);

  const toggleSource = useCallback((id) => {
    setEnabledSources((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }, []);

  const ask = useCallback(async (question) => {
    if (!question.trim() || loading) return;

    if (abortRef.current) abortRef.current.abort();

    const userMsg = { role: 'user', content: question };
    const asstId = Date.now();
    const asstMsg = { id: asstId, role: 'assistant', content: '', thinking: 'Searching knowledge base…', citations: [], trace: [] };

    setMessages((prev) => [...prev, userMsg, asstMsg]);
    setLoading(true);
    setInput('');

    try {
      const stream = api.chat(question);
      let answerText = '';
      let citations = [];
      const trace = [];

      for await (const event of stream) {
        if (event.type === 'retrieval') {
          citations = event.chunks;
          trace.push(`Retrieved ${event.chunks.length} chunks`);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === asstId ? { ...m, thinking: 'Writing the answer…', citations, trace } : m
            )
          );
        } else if (event.type === 'token') {
          answerText += event.text;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === asstId ? { ...m, thinking: null, content: answerText } : m
            )
          );
        } else if (event.type === 'done') {
          trace.push('Answer generated');
          setMessages((prev) =>
            prev.map((m) =>
              m.id === asstId ? { ...m, thinking: null, content: answerText, citations, trace } : m
            )
          );
        }
      }
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === asstId
            ? { ...m, thinking: null, content: `Error: ${err.message}` }
            : m
        )
      );
    } finally {
      setLoading(false);
    }
  }, [loading]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      ask(input);
    }
  };

  const handleIngest = async () => {
    setIngesting(true);
    await api.ingest('all');
    setTimeout(() => setIngesting(false), 3000);
  };

  const healthPill = health === 'ok' ? 'ok' : health === 'checking' ? 'info' : 'bad';
  const healthLabel = health === 'ok' ? '✓ API connected' : health === 'checking' ? '… connecting' : '✗ API offline';

  return (
    <div className="layout">
      <Sidebar
        mode={mode}
        setMode={setMode}
        sources={sources}
        enabledSources={enabledSources}
        toggleSource={toggleSource}
        onIngest={handleIngest}
        ingesting={ingesting}
      />

      <div className="main">
        {/* Status pills */}
        <div className="status-pills">
          <span className={`pill ${healthPill}`}>{healthLabel}</span>
          <span className="pill info">Qdrant · hybrid RRF</span>
          <span className="pill info">BAAI/bge-large-en-v1.5</span>
          <span className="pill info">Claude · cross-encoder rerank</span>
        </div>

        {messages.length === 0 ? (
          <div className="hero">
            <h2>🧪 QABuddy.ai</h2>
            <p>
              Ask anything grounded in your Selenium/Playwright frameworks, test cases,
              Jira tickets, PRDs, and Jenkins logs — with source citations.
            </p>
            <div className="example-grid">
              {EXAMPLES.map((ex, i) => (
                <button key={i} className="example-card" onClick={() => ask(ex)}>
                  {ex}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="thread" ref={threadRef}>
            {messages.map((msg, i) => (
              <Message key={msg.id ?? i} msg={msg} onCiteClick={setViewChunk} />
            ))}
          </div>
        )}

        <div className="composer">
          <div className="composer-inner">
            <textarea
              ref={textareaRef}
              rows={1}
              placeholder="Ask QABuddy… (Enter to send, Shift+Enter for newline)"
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px';
              }}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            <button
              className="send-btn"
              onClick={() => ask(input)}
              disabled={loading || !input.trim()}
            >
              {loading ? '⏳' : 'Ask'}
            </button>
          </div>
        </div>
      </div>

      {viewChunk && <SourceViewer chunk={viewChunk} onClose={() => setViewChunk(null)} />}
    </div>
  );
}
