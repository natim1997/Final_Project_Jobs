const { db } = require('../config/firebase');
const { getAiSemanticScore } = require('../services/aiService');
const { calculateFinalMatchScore } = require('../utils/matchCalculator');
const { calculateScheduleMatch } = require('../utils/scheduleMatcher');
const logger = require('../config/logger');

// ==========================================
// Security & Privacy Helper Functions
// ==========================================

/**
 * Applies Pseudonymisation (GDPR Compliance).
 * Removes PII before sending data to the AI server.
 */
const anonymizeCandidateData = (candidateData, candidateId) => {
    const scrubbedData = JSON.parse(JSON.stringify(candidateData));
    if (scrubbedData.personal_info) {
        delete scrubbedData.personal_info.first_name;
        delete scrubbedData.personal_info.last_name;
        delete scrubbedData.personal_info.email;
        delete scrubbedData.personal_info.phone;
    }
    scrubbedData.candidateId = candidateId;
    return scrubbedData;
};

// ==========================================
// Matchmaking Helper Functions
// ==========================================

/**
 * Calculates distance in KM between two points.
 */
const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371; 
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
};

/**
 * Checks for strict dealbreakers based on candidate settings.
 */
const failsDealbreakers = (candidatePrefs, jobCharacteristics) => {
    if (!candidatePrefs || !jobCharacteristics) return false;
    for (const [key, pref] of Object.entries(candidatePrefs)) {
        if (pref.requested === true && pref.is_dealbreaker === true) {
            if (jobCharacteristics[key] !== true) {
                return true; 
            }
        }
    }
    return false;
};

// ==========================================
// Main Controller
// ==========================================

/**
 * Main function to generate and return job matches for a user.
 */
const getMatchesForCandidate = async (req, res) => {
    try {
        const candidateId = req.params.candidateId;

        // 1. Security Check (Ensure user only requests their own matches)
        if (req.user && req.user.uid !== candidateId) {
            return res.status(403).json({ error: "Access Denied." });
        }

        // 2. Fetch Candidate Profile
        const candidateSnap = await db.ref(`candidates/${candidateId}`).once('value');
        if (!candidateSnap.exists()) {
            return res.status(404).json({ error: "Candidate not found." });
        }
        
        const candidateData = candidateSnap.val();
        const candidateLoc = candidateData.location || {};
        const maxDist = candidateLoc.max_distance_km || 25;
        
        const secureCandidatePayload = anonymizeCandidateData(candidateData, candidateId);

        // 3. Fetch All Available Jobs
        const jobsSnap = await db.ref('jobs').once('value');
        const allJobs = jobsSnap.val() || {};
        let matchResults = [];

        // 4. Processing Loop
        for (const jobId in allJobs) {
            const jobData = allJobs[jobId];
            const jobLoc = jobData.location || {};

            // --- FILTER A: Geo-Distance ---
            if (candidateLoc.lat && jobLoc.lat) {
                const distance = calculateDistance(candidateLoc.lat, candidateLoc.lng, jobLoc.lat, jobLoc.lng);
                if (distance > maxDist) continue; 
                jobData.calculated_distance = Number(distance.toFixed(1));
            }

            // --- FILTER B: Strict Schedule ---
            if (jobData.availability && candidateData.availability) {
                const scheduleScore = calculateScheduleMatch(jobData.availability, candidateData.availability);
                if (scheduleScore < 100) continue; 
            }

            // --- FILTER C: Dealbreakers ---
            if (failsDealbreakers(candidateData.preferences, jobData.characteristics)) {
                continue;
            }

            try {
                // --- STEP D: AI Semantic Scoring ---
                const aiResponse = await getAiSemanticScore(jobData, secureCandidatePayload);
                
                const rawAiScore = (typeof aiResponse === 'object') ? aiResponse.score : aiResponse;
                const aiExplanation = aiResponse.reason || "Match based on your overall profile and skills.";

                // --- STEP E: Final Weighted Score ---
                const finalResult = calculateFinalMatchScore(jobData, candidateData, rawAiScore);

                if (finalResult.finalScore > 0) {
                    matchResults.push({
                        jobId: jobId,
                        job_title: jobData.basic_info?.job_title || "Position",
                        final_match_score: finalResult.finalScore,
                        match_explanation: aiExplanation, 
                        distance_km: jobData.calculated_distance || 0,
                        status: finalResult.status,
                        breakdown: finalResult.breakdown,
                        full_job_data: jobData 
                    });
                }
            } catch (aiError) {
                logger.error(`AI logic error for job ${jobId}: ${aiError.message}`);
            }
        }

        // 5. Sort matches (Highest score first)
        matchResults.sort((a, b) => b.final_match_score - a.final_match_score);

        // 6. Final response
        res.status(200).json({
            success: true,
            total_matches: matchResults.length,
            matches: matchResults 
        });

    } catch (error) {
        logger.error("Matchmaking Error:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
};

module.exports = { getMatchesForCandidate };