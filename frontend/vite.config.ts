import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Permite configurar o backend via env var.
// - Local dev (sem Docker):  VITE_BACKEND_URL=http://localhost:5000
// - Docker compose dev:      VITE_BACKEND_URL=http://backend:5000
const BACKEND_URL = process.env.VITE_BACKEND_URL || "http://localhost:5000";
const WS_URL = BACKEND_URL.replace(/^http/, "ws");

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": "/src",
      src: "/src",
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: BACKEND_URL,
        changeOrigin: true,
      },
      "/ws": {
        target: WS_URL,
        ws: true,
      },
    },
  },
});
