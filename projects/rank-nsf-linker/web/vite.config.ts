import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    // Same routing as web/conf/nginx.conf: /api -> the Go server, prefix stripped.
    proxy: {
      "/api": {
        target: "http://localhost:8080",
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
    },
  },
});
