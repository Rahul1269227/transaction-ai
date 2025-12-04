/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ]
  },
  // Increase server timeout for long-running batch operations
  serverRuntimeConfig: {
    timeout: 300000, // 5 minutes in milliseconds
  },
}

module.exports = nextConfig
