import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["45.76.16.176"],
  turbopack: {
    // `~/dev` holds several projects, each with its own lockfile. Turbopack
    // infers the root from the outermost lockfile, so pin it here.
    root: path.resolve(import.meta.dirname),
    // Browser builds only: workerpool (pulled in by the 3D viewer) requires
    // these behind a Node-only branch it never takes in the browser.
    resolveAlias: {
      child_process: { browser: "./src/lib/empty-module.ts" },
      worker_threads: { browser: "./src/lib/empty-module.ts" },
      os: { browser: "./src/lib/empty-module.ts" },
    },
  },
};

export default nextConfig;
