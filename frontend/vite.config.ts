import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// API base is read from VITE_API_URL at build/runtime; in dev we proxy /api -> backend.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/api": {
        target: process.env.VITE_API_TARGET || "http://localhost:8000",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
    },
  },
});
