const express = require('express');
const router = express.Router();
const { createJob, updateJob, deleteJob } = require('../controllers/jobController');

// Import security middlewares
const { verifyToken, requireRole } = require('../middleware/authMiddleware');
const { validateJobInput } = require('../middleware/validationMiddleware');

// ==========================================
// Protected Employer Routes
// ==========================================



// Pipeline 1: Verify Identity and Role
router.use(verifyToken, requireRole('employer'));

// Route to create a new job posting
// Pipeline 2: Validate Input Data -> Create Job
router.post('/', validateJobInput, createJob);

// Route to update an existing job posting
// Pipeline 2: Validate Input Data -> Update Job
router.put('/:jobId', validateJobInput, updateJob);

// Route to delete a job posting (No body validation needed here)
router.delete('/:jobId', deleteJob);

module.exports = router;