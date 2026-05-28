const { db } = require('../config/firebase');
const logger = require('../config/logger'); // Import custom Winston logger

// ==========================================
// Employer Job Management Controller
// ==========================================

/**
 * Creates a new job posting based on the new employer flow.
 * Supports optional company/category and custom apparel requirements.
 * Security: Automatically assigns the authenticated employer's UID as the owner.
 */
const createJob = async (req, res) => {
    try {
        const employerId = req.user.uid; 
        const rawJobData = req.body;

        // Secure Check: Ensure basic_info and nested job_title exist alongside location
        if (!rawJobData || !rawJobData.basic_info?.job_title || !rawJobData.location) {
            return res.status(400).json({ error: "Missing core job fields: title and location are required." });
        }

        // Construct structured data matching the new employer flow
        const structuredJob = {
            employerId,
            basic_info: {
                job_title: rawJobData.basic_info.job_title,
                company_name: rawJobData.basic_info.company_name || null, // Optional field
                category: rawJobData.basic_info.category || null,         // Optional field
                address: rawJobData.location.address || "",
                lat: rawJobData.location.lat,
                lng: rawJobData.location.lng
            },
            dealbreakers: {
                is_student_only: rawJobData.dealbreakers?.is_student_only || false,
                is_remote: rawJobData.dealbreakers?.is_remote || false,
                requires_license: rawJobData.dealbreakers?.requires_license || false
            },
            availability: rawJobData.availability || {
                sunday: [], monday: [], tuesday: [], wednesday: [], 
                thursday: [], friday: [], saturday: [],
                is_flexible: true // Assume flexible if no strict schedule was provided
            },
            salary_info: {
                amount: rawJobData.salary_info?.amount || 0,
                type: rawJobData.salary_info?.type || "hourly", // hourly or global
                includes_tips: rawJobData.salary_info?.includes_tips || false
            },
            requirements: {
                languages: rawJobData.requirements?.languages || [],
                licenses: rawJobData.requirements?.licenses || [],
                tools: rawJobData.requirements?.tools || [],
                tech_stack: rawJobData.requirements?.tech_stack || [],
                certifications: rawJobData.requirements?.certifications || [],
                min_experience_years: rawJobData.requirements?.min_experience_years || 0
            },
            // Array for dress codes and equipment requirements
            apparel_requirements: rawJobData.apparel_requirements || [], 
            description: rawJobData.description || "",
            created_at: Date.now()
        };

        // Save to Firebase Realtime Database
        const newJobRef = db.ref('jobs').push();
        await newJobRef.set(structuredJob);
        
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

        // Prevent changing the original owner
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