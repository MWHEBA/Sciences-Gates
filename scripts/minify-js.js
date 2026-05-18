#!/usr/bin/env node

/**
 * JavaScript Minification Script
 * 
 * This script minifies all JavaScript files in the static/js directory
 * and outputs them with .min.js extension for production use.
 * 
 * Usage: node scripts/minify-js.js
 */

const fs = require('fs');
const path = require('path');

// Simple JavaScript minification function
// Removes comments, whitespace, and unnecessary characters
function minifyJS(code) {
  // Remove single-line comments
  code = code.replace(/\/\/.*$/gm, '');
  
  // Remove multi-line comments
  code = code.replace(/\/\*[\s\S]*?\*\//g, '');
  
  // Remove leading/trailing whitespace from lines
  code = code.split('\n').map(line => line.trim()).join('\n');
  
  // Remove empty lines
  code = code.replace(/\n\s*\n/g, '\n');
  
  // Remove spaces around operators and punctuation (carefully)
  code = code.replace(/\s*([{}();:,=+\-*/<>!&|?])\s*/g, '$1');
  
  // Restore spaces after keywords
  code = code.replace(/(if|else|for|while|function|return|var|let|const|new|typeof|instanceof)\(/g, '$1 (');
  
  // Remove trailing newlines
  code = code.trim();
  
  return code;
}

// Main minification process
function minifyJSFiles() {
  const jsDir = path.join(__dirname, '..', 'static', 'js');
  
  // Check if directory exists
  if (!fs.existsSync(jsDir)) {
    console.error(`Error: Directory ${jsDir} does not exist`);
    process.exit(1);
  }
  
  // Get all .js files (excluding .min.js files)
  const files = fs.readdirSync(jsDir)
    .filter(file => file.endsWith('.js') && !file.endsWith('.min.js'));
  
  if (files.length === 0) {
    console.log('No JavaScript files to minify');
    return;
  }
  
  console.log(`Minifying ${files.length} JavaScript file(s)...`);
  
  files.forEach(file => {
    const inputPath = path.join(jsDir, file);
    const outputPath = path.join(jsDir, file.replace('.js', '.min.js'));
    
    try {
      // Read the original file
      const code = fs.readFileSync(inputPath, 'utf8');
      
      // Minify the code
      const minified = minifyJS(code);
      
      // Write the minified file
      fs.writeFileSync(outputPath, minified, 'utf8');
      
      // Calculate size reduction
      const originalSize = code.length;
      const minifiedSize = minified.length;
      const reduction = ((1 - minifiedSize / originalSize) * 100).toFixed(2);
      
      console.log(`✓ ${file} → ${file.replace('.js', '.min.js')} (${reduction}% reduction)`);
    } catch (error) {
      console.error(`✗ Error minifying ${file}:`, error.message);
      process.exit(1);
    }
  });
  
  console.log('JavaScript minification complete!');
}

// Run the minification
minifyJSFiles();
