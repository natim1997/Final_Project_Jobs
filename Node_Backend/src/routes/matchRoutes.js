const express = require('express');
const router = express.Router();
const { getMatchesForCandidate } = require('../controllers/matchController');

router.get('/:candidateId', getMatchesForCandidate);

module.exports = router;