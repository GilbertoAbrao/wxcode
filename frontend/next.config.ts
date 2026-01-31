import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  output: "standalone",
  reactStrictMode: false,
  turbopack: {
    // Set root to wxcode workspace to prevent inferring /Users/gilberto
    root: path.resolve(__dirname, ".."),
  },
};

export default nextConfig;
