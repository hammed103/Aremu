#!/usr/bin/env node

// Simple startup script for Railway deployment
// This script changes to the FE directory and starts the frontend server

const { spawn } = require('child_process');
const path = require('path');

console.log('🚀 Starting Aremu Frontend...');
console.log('📁 Changing to FE directory...');

// Change to FE directory and start the server
const feDir = path.join(__dirname, 'FE');
process.chdir(feDir);

console.log('📦 Installing dependencies...');
const install = spawn('npm', ['install'], { stdio: 'inherit' });

install.on('close', (code) => {
  if (code !== 0) {
    console.error('❌ Failed to install dependencies');
    process.exit(1);
  }
  
  console.log('✅ Dependencies installed');
  console.log('🌐 Starting server...');
  
  // Start the server
  const server = spawn('npm', ['start'], { stdio: 'inherit' });
  
  server.on('close', (code) => {
    console.log(`Server exited with code ${code}`);
    process.exit(code);
  });
});
