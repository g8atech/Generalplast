import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";
import site from "./src/config/site.json" with { type: "json" };

export default defineConfig({
  site: site.site.url,
  trailingSlash: "never",
  build: { format: "file" },
  vite: { plugins: [tailwindcss()] },
});
