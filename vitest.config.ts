import { defineConfig } from "vitest/config";
import path from "node:path";

/**
 * - `server-only` is aliased to a no-op so server modules load under Node.
 * - `@/…` mirrors the tsconfig alias. Library code under src/lib uses relative
 *   imports (Wildcat consumes it as a package); the alias is for the app.
 * - `*.exec.test.ts` call live models or the Python service and skip
 *   themselves when the key or service is absent.
 */
export default defineConfig({
  resolve: {
    alias: {
      "server-only": path.resolve(__dirname, "test/stubs/server-only.ts"),
      "@": path.resolve(__dirname, "src"),
    },
  },
  test: {
    environment: "node",
    // `figure-image.ts` reads local figures only when a corpus root is named.
    env: { GEOLOGY_CORPUS_ROOT: path.resolve(__dirname, "geology-corpus") },
    include: ["src/**/*.test.ts", "test/**/*.test.ts"],
    clearMocks: true,
  },
});
