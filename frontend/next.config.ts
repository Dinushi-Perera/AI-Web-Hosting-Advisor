import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // Emit the minimal self-contained server used by the production container.
  output: "standalone",
};

export default nextConfig;
