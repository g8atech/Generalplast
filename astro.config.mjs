import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";
import site from "./src/config/site.json" with { type: "json" };

export default defineConfig({
  site: site.site.url,
  trailingSlash: "never",
  // Una cartella per pagina (/pagina/index.html): così gli indirizzi senza
  // estensione funzionano su qualsiasi hosting, non solo dove è attiva la
  // rimozione automatica del ".html".
  build: { format: "directory" },
  vite: { plugins: [tailwindcss()] },
});
