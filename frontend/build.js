const fs = require('fs');
const path = require('path');

// Create build directory
const buildDir = path.join(__dirname, 'build');
if (!fs.existsSync(buildDir)) {
  fs.mkdirSync(buildDir, { recursive: true });
}

// Copy and process HTML
const htmlContent = fs.readFileSync(path.join(__dirname, 'public', 'index.html'), 'utf8');
fs.writeFileSync(path.join(buildDir, 'index.html'), htmlContent);

// Copy CSS if exists
const cssPath = path.join(__dirname, 'public', 'styles.css');
if (fs.existsSync(cssPath)) {
  fs.copyFileSync(cssPath, path.join(buildDir, 'styles.css'));
}

console.log('Build completed successfully!');
