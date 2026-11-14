/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies API calls the same way the production nginx does.
// BOOKING_URL / ASSISTANT_URL point at the compose services (or localhost ports).
const booking = process.env.BOOKING_URL ?? "http://localhost:8000";
const assistant = process.env.ASSISTANT_URL ?? "http://localhost:8001";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      "/api/v1/assistant": { target: assistant, changeOrigin: true },
      "/api": { target: booking, changeOrigin: true },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
