import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const nextConfig: NextConfig = {
  reactCompiler: true,
  // Self-contained server in .next/standalone, for the Docker image (see Dockerfile).
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : undefined,
};

export default createNextIntlPlugin("./src/i18n/request.ts")(nextConfig);
