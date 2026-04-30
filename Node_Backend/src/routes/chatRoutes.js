const express = require('express');
const router = express.Router();
const { sendMessage, getMessages } = require('../controllers/chatController');

// POST request to send a message
// http://localhost:3000/api/chats/send
router.post('/send', sendMessage);

// GET request to fetch chat history (Memory Optimized)
// http://localhost:3000/api/chats/history/cand999/job_bonus
router.get('/history/:candidateId/:jobId', getMessages);

module.exports = router;