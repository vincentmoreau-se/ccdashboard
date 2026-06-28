import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["src/test/setup.ts"],
    // Vitest runs unit tests under src/; Playwright e2e specs in tests/e2e
    // are executed by `playwright test`, not vitest.
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
  },
});
