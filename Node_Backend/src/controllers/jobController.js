const { db } = require('../config/firebase');
const logger = require('../config/logger'); 
const { calculateFinalMatchScore } = require('../utils/matchCalculator'); 
const { triggerAllCandidatesMatch } = require('../services/backgroundMatcher');

// ==========================================
// Employer Job Management Controller
// ==========================================

const createJob = async (req, res) => {
    try {
        // Generate a new document reference to get a unique ID from Firestore
        const jobRef = db.collection('jobs').doc();
        const jobId = jobRef.id;
        
        // Link the job to the user who created it
        const employerId = req.body.employerId || (req.user ? req.user.uid : "test_employer_id");
        
        const data = req.body;

        if (!data.title || !data.category || !data.company) {
            return res.status(400).json({ error: "Missing core job fields: title, category, or company." });
        }

        const structuredJob = {
            id: jobId,
            employerId: employerId,
            address: data.address || "",
            category: data.category || "", 
            company: data.company || "",
            description: data.description || "",
            date: data.date || "", 
            startTime: data.startTime || "",
            endTime: data.endTime || "",
            imageUrl: data.imageUrl || "", 
            isUrgent: data.isUrgent || false,
            link: data.link || "",
            phone: data.phone || "",
            requirements: data.requirements || "",
            salary: parseFloat(data.salary) || 0.0,
            salaryType: data.salaryType || "hourly",
            title: data.title || "",
            workerNeeded: parseInt(data.workerNeeded) || 1,
            workersRegistered: data.workersRegistered || 0,
            createdAt: Date.now()
        };

        // Save to Firestore
        await jobRef.set(structuredJob);
        
        // NEW - Trigger AI to find matches for this specific new job
        triggerAllCandidatesMatch(jobId);
        
        logger.info(`Job Created: ID ${jobId} with category ${structuredJob.category}`);
        return res.status(201).json({ message: "Job created successfully!", jobId: jobId });

    } catch (error) {
        logger.error(`Error creating job: ${error.message}`);
        return res.status(500).json({ error: "Internal server error" });
    }
};

const updateJob = async (req, res) => {
    try {
        const { jobId } = req.params;
        const employerId = req.user ? req.user.uid : "test_employer_id";
        const updateData = req.body;

        const jobRef = db.collection('jobs').doc(jobId);
        const doc = await jobRef.get();

        if (!doc.exists) {
            return res.status(404).json({ error: "Job not found." });
        }

        if (doc.data().employerId !== employerId && doc.data().employerId !== "test_employer_id") {
            return res.status(403).json({ error: "Forbidden: You do not have permission to edit this job." });
        }

        delete updateData.id;
        delete updateData.employerId;
        updateData.updatedAt = Date.now();

        await jobRef.update(updateData);

        //Trigger AI because job requirements or details changed
        triggerAllCandidatesMatch();

        return res.status(200).json({ status: "success", message: "Job updated successfully." });
    } catch (error) {
        logger.error(`Internal Error in updateJob: ${error.message}`);
        return res.status(500).json({ error: "Internal Server Error" });
    }
};

const deleteJob = async (req, res) => {
    try {
        const { jobId } = req.params;
        const employerId = req.user ? req.user.uid : "test_employer_id";

        const jobRef = db.collection('jobs').doc(jobId);
        const doc = await jobRef.get();

        if (!doc.exists) {
            return res.status(404).json({ error: "Job not found." });
        }

        if (doc.data().employerId !== employerId && doc.data().employerId !== "test_employer_id") {
            return res.status(403).json({ error: "Forbidden: You can only delete your own jobs." });
        }

        await jobRef.delete();

        return res.status(200).json({ status: "success", message: "Job deleted successfully." });
    } catch (error) {
        logger.error(`Internal Error in deleteJob: ${error.message}`);
        return res.status(500).json({ error: "Internal Server Error" });
    }
};

const getJobCandidates = async (req, res) => {
    try {
        const { jobId } = req.params;
        
        const jobDoc = await db.collection('jobs').doc(jobId).get();
        if (!jobDoc.exists) {
            return res.status(404).json({ error: "Job not found." });
        }
        const job = jobDoc.data();

        const candidatesSnapshot = await db.collection('candidates').get();
        if (candidatesSnapshot.empty) {
            return res.status(200).json({ success: true, total_matches: 0, matches: [] });
        }

        const matchedCandidates = [];

        candidatesSnapshot.forEach(doc => {
            const candidate = doc.data();
            
            // Skip this candidate if they are the employer who posted the job!
            if (candidate.id === job.employerId) {
                return; 
            }

            const aiSemanticScore = 80; 
            const matchResult = calculateFinalMatchScore(job, candidate, aiSemanticScore);

            if (matchResult.status === "MATCH" || matchResult.status === "POTENTIAL") {
                matchedCandidates.push({
                    candidateId: candidate.id,
                    name: candidate.name || "Unknown Candidate",
                    phone: candidate.phone || "No phone",
                    email: candidate.email || "No email",
                    bio: candidate.bio || "",
                    final_match_score: matchResult.finalScore,
                    status: matchResult.status,
                    breakdown: matchResult.breakdown
                });
            }
        });

        matchedCandidates.sort((a, b) => b.final_match_score - a.final_match_score);

        return res.status(200).json({
            success: true,
            job_title: job.title,
            total_matches: matchedCandidates.length,
            matches: matchedCandidates
        });

    } catch (error) {
        logger.error(`Error fetching candidates for job: ${error.message}`);
        return res.status(500).json({ error: "Internal server error" });
    }
};

module.exports = { createJob, updateJob, deleteJob, getJobCandidates };