const express = require('express');
const path = require('path');
const app = express();

app.use(express.json());
app.use(express.static(path.join(__dirname, 'frontend')));

// API routes
app.use('/api/login', require('./routes/login'));

// Default to login.html
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend', 'login.html'));
});

// Start server
app.listen(5000, () => console.log("Server running on http://localhost:5000"));
