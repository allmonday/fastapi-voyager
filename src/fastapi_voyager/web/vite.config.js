import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"

export default defineConfig({
  plugins: [vue()],
  root: ".",
  base: process.env.VITE_BASE_PATH || "fastapi-voyager-static/dist/",
  build: {
    outDir: "dist",
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: {
          "vue-vendor": ["vue"],
          "naive-vendor": ["naive-ui"],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/dot": "http://localhost:8000",
      "/er-diagram": "http://localhost:8000",
      "/schema": "http://localhost:8000",
      "/source": "http://localhost:8000",
      "/vscode-link": "http://localhost:8000",
      "/route": "http://localhost:8000",
      "/voyager": "http://localhost:8000",
    },
  },
})
