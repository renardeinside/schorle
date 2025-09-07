import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    externalDir: true,
  },
  allowedDevOrigins: ["127.0.0.1", "0.0.0.0", "localhost"],
};

export default nextConfig;
