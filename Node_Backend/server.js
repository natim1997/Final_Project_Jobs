require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet'); // Security headers
const morgan = require('morgan'); // Request logging
const rateLimit = require('express-rate-limit');
const logger = require('./src/config/logger'); // Our custom Winston logger

// Initialize Firebase configuration
require('./src/config/firebase'); 

const app = express();
const PORT = process.env.PORT || 3000;

// ==========================================
// Core Security Middleware
// ==========================================

// Use Helmet to secure Express apps by setting various HTTP headers
app.use(helmet()); 

// Use CORS to handle cross-origin requests
app.use(cors()); 

// Parse incoming JSON payloads
app.use(express.json()); 

// ==========================================
// Logging Middleware
// ==========================================

// Use Morgan to log all HTTP requests via our Winston logger
app.use(morgan('combined', { 
    stream: { write: (message) => logger.info(message.trim()) } 
}));

// ==========================================
// Rate Limiting
// ==========================================

const apiLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // Limit each IP to 100 requests per window
    message: {
        error: "Too many requests from this IP. Please try again after 15 minutes.",
        status: 429
    },
    standardHeaders: true,
    legacyHeaders: false,
});

// Apply rate limiting to all API routes
app.use('/api/', apiLimiter);

// ==========================================
// Routes
// ==========================================

// Basic health check route
app.get('/health', (req, res) => {
    res.status(200).json({ 
        status: 'success', 
        message: 'Node.js Backend is running smoothly!' 
    });
});

// Connect Application Routes
app.use('/api/candidates', require('./src/routes/candidateRoutes'));
app.use('/api/jobs', require('./src/routes/jobRoutes'));
app.use('/api/matches', require('./src/routes/matchRoutes'));
app.use('/api/reviews', require('./src/routes/reviewRoutes'));
app.use('/api/favorites', require('./src/routes/favoriteRoutes'));
app.use('/api/chats', require('./src/routes/chatRoutes'));

// ==========================================
// Start Server
// ==========================================
app.listen(PORT, () => {
    logger.info(`Node.js Server started and running on port ${PORT}`);
    console.log(`Node.js Server is running on port ${PORT}`);
    console.log(`Configured to talk to AI Server at: ${process.env.AI_SERVER_URL}`);
});