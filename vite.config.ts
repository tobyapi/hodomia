import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  server: { host: "127.0.0.1", port: 1430, strictPort: true, watch: { ignored: ["**/src-tauri/**", "**/.runtime/**", "**/test-results/**", "**/projects/**"] } },
  envPrefix: ["VITE_", "TAURI_ENV_"],
  build: { target: "chrome105", sourcemap: !!process.env.TAURI_ENV_DEBUG },
  test: { environment: "jsdom", setupFiles: ["./src/test/setup.ts"] },
});
