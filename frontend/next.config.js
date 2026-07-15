/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const dest = process.env.INTERNAL_API_URL || "http://localhost:8000";
    return [
      {
        source: '/api/:path*',
        destination: `${dest}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;