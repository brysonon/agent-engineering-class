import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve("app") } },
  test: {
    environment: "node",
    setupFiles: ["./app/test/setup.ts"],
    include: ["app/**/*.test.{ts,tsx}"],
    coverage: { reporter: ["text"] }
  }
});
