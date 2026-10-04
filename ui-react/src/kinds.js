export const KIND = {
  testcases:     { icon: '🧪', color: '#2f7d4f', bg: '#eaf6ee', label: 'Test case' },
  test_cases:    { icon: '🧪', color: '#2f7d4f', bg: '#eaf6ee', label: 'Test case' },
  jira:          { icon: '🐞', color: '#2563eb', bg: '#eaf1fe', label: 'Jira' },
  docs:          { icon: '📄', color: '#b45309', bg: '#fdf3e4', label: 'Doc' },
  transcript:    { icon: '🗓️', color: '#7c3aed', bg: '#f3eefe', label: 'Meeting' },
  meeting_notes: { icon: '🗓️', color: '#7c3aed', bg: '#f3eefe', label: 'Meeting' },
  diagram:       { icon: '🔷', color: '#0e7490', bg: '#e6f5f8', label: 'Diagram' },
  logs:          { icon: '🧯', color: '#c2410c', bg: '#fdeee6', label: 'CI log' },
  jenkins_logs:  { icon: '🧯', color: '#c2410c', bg: '#fdeee6', label: 'CI log' },
  code:          { icon: '⌨️', color: '#4338ca', bg: '#eeeffd', label: 'Code' },
  selenium:      { icon: '⌨️', color: '#4338ca', bg: '#eeeffd', label: 'Selenium' },
  playwright:    { icon: '⌨️', color: '#6d28d9', bg: '#ede9fe', label: 'Playwright' },
  figma:         { icon: '🎨', color: '#be185d', bg: '#fdecf4', label: 'Figma' },
  prd:           { icon: '📋', color: '#0369a1', bg: '#e0f2fe', label: 'PRD' },
};

export const kindOf = (k) =>
  KIND[k] || { icon: '•', color: '#6f6b60', bg: '#f1efe8', label: k || 'source' };
