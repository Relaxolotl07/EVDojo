window.api = {
  post: (url, body) => fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(r => r.json()),
  get: (url) => fetch(url).then(r => r.json()),
};
window.qs = (k) => new URLSearchParams(location.search).get(k);
window.redact = (s) => (s || '').replace(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g, '[email]');

