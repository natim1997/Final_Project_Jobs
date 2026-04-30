const { db } = require('../config/firebase');
const logger = require('../config/logger'); // Import our custom Winston logger

// ==========================================
// Employer Job Management Controller
// ==========================================

/**
 * Creates a new job posting.
 * Security: Automatically assigns the authenticated employer's UID as the owner.
 */
const createJob = async (req, res) => {
    try {
        const employerId = req.user.uid; 
        const jobData = req.body;

        if (!jobData) {
            return res.status(400).json({ error: "Missing job data." });
        }

        // If the employer did not provide a specific schedule, set a default empty structure
        if (!jobData.availability) {
            jobData.availability = {
                sunday: [], monday: [], tuesday: [], wednesday: [], 
                thursday: [], friday: [], saturday: [],
                is_flexible: true // Assume flexible if no strict schedule was provided
            };
        }

        // Enforce ownership and set timestamps
        jobData.employerId = employerId;
        jobData.created_at = Date.now();

        // Save to Firebase Realtime Database
        const newJobRef = db.ref('jobs').push();
        await newJobRef.set(jobData);
        
        return res.status(201).json({ message: "Job created successfully with schedule!", jobId: newJobRef.key });
    } catch (error) {
        console.error("Error creating job:", error);
        return res.status(500).json({ error: "Internal server error" });
    }
};
/**
 * Updates an existing job posting.
 * Security: Verifies ownership to prevent IDOR attacks.
 */
const updateJob = async (req, res) => {
    try {
        const { jobId } = req.params;
        const employerId = req.user.uid;
        const updateData = req.body;

        const jobRef = db.ref(`jobs/${jobId}`);
        const snapshot = await jobRef.once('value');

        if (!snapshot.exists()) {
            return res.status(404).json({ error: "Job not found." });
        }

        const existingJob = snapshot.val();

        // IDOR Protection: Security logging for unauthorized attempts
        if (existingJob.employerId !== employerId) {
            logger.error(`SECURITY ALERT: Unauthorized update attempt on job ${jobId} by user ${employerId}`);
            return res.status(403).json({ error: "Forbidden: You do not have permission to edit this job." });
        }

        delete updateData.employerId;
        updateData.updated_at = Date.now();

        await jobRef.update(updateData);

        logger.info(`Job Updated: ID ${jobId} by Employer ${employerId}`);
        res.status(200).json({ status: "success", message: "Job updated successfully." });

    } catch (error) {
        logger.error(`Internal Error in updateJob: ${error.message}`);
        res.status(500).json({ error: "Internal Server Error" });
    }
};

/**
 * Deletes a job posting.
 * Security: Verifies ownership before removal.
 */
const deleteJob = async (req, res) => {
    try {
        const { jobId } = req.params;
        const employerId = req.user.uid;

        const jobRef = db.ref(`jobs/${jobId}`);
        const snapshot = await jobRef.once('value');

        if (!snapshot.exists()) {
            return res.status(404).json({ error: "Job not found." });
        }

        // IDOR Protection: Security logging for unauthorized deletion attempts
        if (snapshot.val().employerId !== employerId) {
            logger.error(`SECURITY ALERT: Unauthorized deletion attempt on job ${jobId} by user ${employerId}`);
            return res.status(403).json({ error: "Forbidden: You can only delete your own jobs." });
        }

        await jobRef.remove();

        logger.info(`Job Deleted: ID ${jobId} by Employer ${employerId}`);
        res.status(200).json({ status: "success", message: "Job deleted successfully." });

    } catch (error) {
        logger.error(`Internal Error in deleteJob: ${error.message}`);
        res.status(500).json({ error: "Internal Server Error" });
    }
};

module.exports = { createJob, updateJob, deleteJob };