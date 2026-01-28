import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  output: "standalone",
  reactStrictMode: false,
  turbopack: {
    root: path.resolve(__dirname),
    resolveAlias: {
      tailwindcss: path.resolve(__dirname, "node_modules/tailwindcss"),
      "tw-animate-css": path.resolve(__dirname, "node_modules/tw-animate-css"),
      "@/styles": path.resolve(__dirname, "src/styles"),
    },
  },
};

export default nextConfig;
