import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
    plugins: [react(), tailwindcss()],
    base: "./",
    build: {
        outDir: "../src/lare/static",
        emptyOutDir: true,
    },
    server: {
        proxy: {
            "/api": "http://127.0.0.1:8741",
            "/images": "http://127.0.0.1:8741",
        },
    },
});
