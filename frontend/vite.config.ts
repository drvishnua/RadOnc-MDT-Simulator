import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const localApiProxy = {
  "/api": {
    target: "http://127.0.0.1:8000",
    changeOrigin: false
  },
  "/health": {
    target: "http://127.0.0.1:8000",
    changeOrigin: false
  }
};

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: localApiProxy
  },
  preview: {
    host: "127.0.0.1",
    port: 4173,
    strictPort: true,
    proxy: localApiProxy
  }
});
