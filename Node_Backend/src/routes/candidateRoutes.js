const express = require('express');
const router = express.Router();
const { saveCandidate } = require('../controllers/candidateController');

// POST request to save a new candidate
// Full URL will be: POST http://localhost:3000/api/candidates
router.post('/', saveCandidate);

module.exports = router;