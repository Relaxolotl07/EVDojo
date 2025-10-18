/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // Proxy API calls during dev to FastAPI to avoid CORS and env setup
    const backend = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
    // Only enable proxy when using localhost backend
    if (backend.startsWith('http://localhost') || backend.startsWith('http://127.0.0.1')) {
      return [{ source: '/api/:path*', destination: `${backend}/:path*` }];
    }
    return [];
  },
};

module.exports = nextConfig;
