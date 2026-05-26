// Script para generar íconos PWA simples
const fs = require('fs');
const path = require('path');

// Crear SVG base
const createSVGIcon = (size) => {
  return `<svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
  <rect width="${size}" height="${size}" fill="#1f2937"/>
  <text x="50%" y="50%" font-family="Arial, sans-serif" font-size="${size/4}" font-weight="bold" 
        text-anchor="middle" dominant-baseline="middle" fill="white">FASA</text>
</svg>`;
};

// Crear archivos SVG
const sizes = [64, 192, 512];
const publicDir = path.join(__dirname, 'public');

sizes.forEach(size => {
  const svgContent = createSVGIcon(size);
  const filename = `pwa-${size}x${size}.svg`;
  fs.writeFileSync(path.join(publicDir, filename), svgContent);
  console.log(`Created ${filename}`);
});

console.log('✅ SVG icons created successfully!');
console.log('📝 Update vite.config.js to use these SVG icons for better compatibility');
