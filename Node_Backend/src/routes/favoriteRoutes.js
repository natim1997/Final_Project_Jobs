const express = require('express');
const router = express.Router();
const { addFavorite, removeFavorite } = require('../controllers/favoriteController');

// POST http://localhost:3000/api/favorites/add
router.post('/add', addFavorite);

// POST http://localhost:3000/api/favorites/remove
router.post('/remove', removeFavorite);

module.exports = router;