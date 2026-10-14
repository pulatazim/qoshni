import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// brauzerdan CORS'siz ishlash uchun API /api ostidan proksilanadi.
const apiTarget = process.env.QOSHNI_API_TARGET ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    // Windows bind mount'ida inotify ishlamaydi — fayllar so'rov bilan kuzatiladi.
    watch: { usePolling: true },
    proxy: { "/api": { target: apiTarget, changeOrigin: true } },
  },
});
