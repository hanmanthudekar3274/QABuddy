const BASE = '/api';

async function* chatStream(question, topK = 8) {
  const resp = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k: topK }),
  });

  if (!resp.ok) {
    const err = await resp.text();
    throw new Error(`API error ${resp.status}: ${err}`);
  }

  const data = await resp.json();
  const { answer, citations = [] } = data;

  if (citations.length) {
    yield { type: 'retrieval', chunks: citations.map((c) => ({
      id: c.source_file,
      source_type: c.source_type,
      source_file: c.source_file,
      text: c.text_preview || '',
      score: c.score ?? 1,
    })) };
  }

  // Emit answer token-by-token for a streaming feel
  const words = answer.split(' ');
  for (let i = 0; i < words.length; i++) {
    yield { type: 'token', text: (i === 0 ? '' : ' ') + words[i] };
  }

  yield { type: 'done' };
}

export const api = {
  async health() {
    try {
      const r = await fetch(`${BASE}/health`);
      return r.ok ? await r.json() : { status: 'error' };
    } catch {
      return { status: 'error' };
    }
  },

  async sources() {
    // Local API has no /sources endpoint — return static list matching data/ folders
    return [
      { id: 'selenium',      label: 'Selenium Framework',  icon: '⌨️' },
      { id: 'playwright',    label: 'Playwright Framework', icon: '⌨️' },
      { id: 'test_cases',   label: 'Test Cases',           icon: '🧪' },
      { id: 'jira',          label: 'Jira Tickets',         icon: '🐞' },
      { id: 'docs',          label: 'Company Docs',         icon: '📄' },
      { id: 'figma',         label: 'Figma Designs',        icon: '🎨' },
      { id: 'meeting_notes', label: 'Meeting Notes',        icon: '🗓️' },
      { id: 'prd',           label: 'PRD / SRS / BRD',      icon: '📋' },
      { id: 'jenkins_logs',  label: 'Jenkins Logs',         icon: '🧯' },
    ];
  },

  chat: chatStream,

  async ingest(source = 'all') {
    const r = await fetch(`${BASE}/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source }),
    });
    return r.ok ? await r.json() : { status: 'error' };
  },

  async chunk(id) {
    // No chunk endpoint in local API — return null
    return null;
  },
};
