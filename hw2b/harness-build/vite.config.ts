import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  root: path.resolve("app/client"),
  plugins: [react()],
  build: { outDir: path.resolve("dist/client"), emptyOutDir: true },
  server: { port: 5173, proxy: { "/api": "http://localhost:8787" } }
});
