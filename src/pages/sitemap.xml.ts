import type { APIRoute } from "astro";
import site from "../config/site.json";

const routes = ["/", "/lavorazione-produzione", "/stampaggio-conto-terzi", "/privacy"];

export const GET: APIRoute = () => {
  const now = new Date().toISOString().slice(0, 10);
  const urls = routes
    .map((r) => {
      const loc = new URL(r, site.site.url).href;
      const priority = r === "/" ? "1.0" : r === "/privacy" ? "0.3" : "0.8";
      return `  <url><loc>${loc}</loc><lastmod>${now}</lastmod><priority>${priority}</priority></url>`;
    })
    .join("\n");
  return new Response(
    `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`,
    { headers: { "Content-Type": "application/xml; charset=utf-8" } },
  );
};
