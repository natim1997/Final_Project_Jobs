const express = require('express');
const router = express.Router();
const { getMatchesForCandidate } = require('../controllers/matchController');

// Import the security middleware functions
const { verifyToken, requireRole } = require('../middleware/authMiddleware');

/**
 * Route: GET /api/matches/:candidateId
 * Security restored:
 * 1. verifyToken: Validates Firebase Authentication JWT.
 * 2. requireRole('candidate'): Ensures only candidates access this logic.
 */
router.get('/:candidateId', verifyToken, requireRole('candidate'), getMatchesForCandidate);

module.exports = router;