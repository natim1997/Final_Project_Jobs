const express = require('express');
const router = express.Router();

const { createJob, updateJob, deleteJob, getJobCandidates } = require('../controllers/jobController');

// Route to create a new job posting
router.post('/', createJob);

// Route to update an existing job posting
router.put('/:jobId', updateJob);

// Route to delete a job posting
router.delete('/:jobId', deleteJob);

// Route to fetch all matching candidates for a specific job
router.get('/:jobId/candidates', getJobCandidates);

module.exports = router;
