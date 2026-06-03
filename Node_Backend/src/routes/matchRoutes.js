const express = require('express');
const router = express.Router();
const { getMatchesForCandidate } = require('../controllers/matchController');

/**
 * Route: GET /api/matches/:candidateId
 * Note: Middleware disabled for prototype demo.
 */
router.get('/:candidateId', getMatchesForCandidate);

module.exports = router;