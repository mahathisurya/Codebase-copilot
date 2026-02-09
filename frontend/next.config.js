/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  eslint: {
    // Don't fail build on ESLint errors in production
    ignoreDuringBuilds: false,
  },
  typescript: {
    // Don't fail build on TypeScript errors in production
    ignoreBuildErrors: false,
  },
  // Disable static page generation errors for error pages
  staticPageGenerationTimeout: 120,
}

module.exports = nextConfig