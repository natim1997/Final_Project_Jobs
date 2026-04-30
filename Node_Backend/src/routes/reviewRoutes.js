const express = require('express');
const router = express.Router();
const { addReview } = require('../controllers/reviewController');

// POST http://localhost:3000/api/reviews
router.post('/', addReview);

module.exports = router;