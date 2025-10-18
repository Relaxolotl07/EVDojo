export default {
  async fetch(request, env, ctx) {
    // Simple proxy to origin API (FastAPI backend)
    // Configure ORIGIN in wrangler.toml (e.g., https://api.evdojo.com or your host)
    const url = new URL(request.url);
    const dest = new URL(url.pathname.replace(/^\/api\//, '/'), env.ORIGIN);
    dest.search = url.search;

    const headers = new Headers(request.headers);
    // Pass through client IP for backend logs
    if (!headers.has('cf-connecting-ip') && request.headers.get('CF-Connecting-IP')) {
      headers.set('cf-connecting-ip', request.headers.get('CF-Connecting-IP'));
    }
    const init = { method: request.method, headers, body: request.body, redirect: 'follow' };
    return fetch(dest.toString(), init);
  }
};

