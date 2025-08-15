// vite.config.js
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiBase = env.VITE_API_BASE || "http://127.0.0.1:5000";

  return {
    plugins: [react()],
    server: {
      port: 5173,
      open: true,
      proxy: {
        // Forward dev requests like /api/parking/... to Flask
        "/api": {
          target: apiBase,
          changeOrigin: true,
          secure: false,
        },
      },
    },
    preview: {
      port: 4173,
      open: true,
    },
    define: {
      // Inject the VITE_ env variables into client bundle
      "process.env": env,
    },
  };
});
