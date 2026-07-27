const express = require('express');
const router = express.Router();
const multer = require('multer');
const { createCandidate } = require('../controllers/candidateController');

// Configure multer to hold the file in memory
const upload = multer({ storage: multer.memoryStorage() });

// Route to create a candidate (expects 'cv_file' as the file field)
router.post('/', upload.single('cv_file'), createCandidate);

module.exports = router;