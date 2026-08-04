import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  // All /api/* requests are handled by app/api/[...proxy]/route.ts
  // which streams the body with no size limit, supporting large file uploads.
  // DO NOT add a /api rewrite here -- the Route Handler takes precedence.
  experimental: {
    proxyTimeout: 300_000, // 5 minutes
  },
};

export default nextConfig;

