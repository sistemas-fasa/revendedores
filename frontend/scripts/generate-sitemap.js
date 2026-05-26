import fs from 'fs'
import path from 'path'

const BASE = process.env.SITE_URL || 'https://example.com'
const routes = ['/', '/login', '/productos', '/carrito', '/pedidos', '/dashboard']

function buildUrl(route) {
  return `${BASE.replace(/\/$/, '')}${route}`
}

const urls = routes.map(r => `  <url>\n    <loc>${buildUrl(r)}</loc>\n  </url>`).join('\n')

const sitemap = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>`

const outDir = path.resolve(process.cwd(), 'public')
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true })
const outPath = path.join(outDir, 'sitemap.xml')
fs.writeFileSync(outPath, sitemap, 'utf8')
console.log('Wrote sitemap to', outPath)
