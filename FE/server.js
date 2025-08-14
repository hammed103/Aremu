const express = require('express');
const path = require('path');
const app = express();

// Get port from environment variable or default to 3000
const PORT = process.env.PORT || 3000;

// Serve static files from the current directory
app.use(express.static('.'));

// Handle SPA routing - serve index.html for all routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Start the server
app.listen(PORT, () => {
  console.log(`🚀 Aremu frontend server running on port ${PORT}`);
  console.log(`📱 Access your app at: http://localhost:${PORT}`);
});
