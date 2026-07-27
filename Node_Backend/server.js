require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const logger = require('./src/config/logger');
const multer = require('multer');
const pdfParse = require('pdf-parse');

// Initialize Firebase configuration
require('./src/config/firebase');

const app = express();
// Use Cloud Run port or default to 8080 locally
const PORT = process.env.PORT || 8080;

// Trust proxy for correct IP detection in production
app.set('trust proxy', 1);

// ==========================================
// Middleware Setup
// ==========================================

// Secure HTTP headers
app.use(helmet());

// Enable cross-origin requests for the frontend
app.use(cors({ origin: '*' }));

// Enable JSON parsing for request bodies
app.use(express.json());

// Logging all requests
app.use(morgan('combined', {
    stream: { write: (message) => logger.info(message.trim()) }
}));

// Limit API usage to prevent abuse
const apiLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 100,
    message: { error: "Too many requests. Please try again later.", status: 429 },
    standardHeaders: true,
    legacyHeaders: false,
});

app.use('/api/', apiLimiter);

// ==========================================
// Routes
// ==========================================

// Health check endpoint
app.get('/health', (req, res) => {
    res.status(200).json({ status: 'success', message: 'Node.js Backend is running' });
});

// Application API routes
app.use('/api/candidates', require('./src/routes/candidateRoutes'));
app.use('/api/jobs', require('./src/routes/jobRoutes'));
app.use('/api/matches', require('./src/routes/matchRoutes'));

// ==========================================
// CV Extraction Route
// ==========================================

const upload = multer({ storage: multer.memoryStorage() });

app.post('/api/extract-cv', upload.single('cv_file'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'No file uploaded' });
        }

        // Process PDF buffer to extract text
        const pdfData = await pdfParse(req.file.buffer);
        const cleanText = pdfData.text.replace(/\n/g, ' ').replace(/\s+/g, ' ').trim();

        res.status(200).json({
            message: 'CV extracted successfully',
            extracted_text: cleanText
        });

    } catch (error) {
        logger.error(`Error extracting CV: ${error.message}`);
        res.status(500).json({ error: 'Failed to process the PDF file' });
    }
});

// ==========================================
// Start Server
// ==========================================

// Listen on 0.0.0.0 so Google Cloud Run can route traffic to this container
app.listen(PORT, '0.0.0.0', () => {
    logger.info(`Node.js Server started on port ${PORT}`);
    console.log(`Node.js Server is running on port ${PORT}`);
});