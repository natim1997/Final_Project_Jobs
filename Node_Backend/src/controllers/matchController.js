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
        delete scrubbedData.personal_info.full_name;
        delete scrubbedData.personal_info.email;
        delete scrubbedData.personal_info.phone;
    }
    scrubbedData.candidateId = candidateId;
    return scrubbedData;
};

// ==========================================
// Matchmaking Helper Functions & Normalization
// ==========================================

/**
 * Normalizes raw job data from Firebase into a strict structured object.
 * This prevents inline bugs and ensures all down-stream logic can trust the schema.
 */
const normalizeJobData = (rawJob, jobId) => {
    // Handle cases where description might be nested in text_fields accidentally
    const description = rawJob.description || rawJob.text_fields?.description || "";
    
    // Clean string quotes if they were added manually in Firebase UI
    const cleanDescription = description.replace(/^"|"$/g, '');

    return {
        jobId: jobId,
        description: cleanDescription,
        apparel_requirements: rawJob.apparel_requirements || [],
        availability: rawJob.availability || null,
        characteristics: rawJob.characteristics || {},
        dealbreakers: rawJob.dealbreakers || {},
        location: {
            lat: rawJob.location?.lat || rawJob.basic_info?.lat || null,
            lng: rawJob.location?.lng || rawJob.basic_info?.lng || null
        },
        requirements: {
            tech_stack: rawJob.requirements?.tech_stack || [],
            languages: rawJob.requirements?.languages || [],
            min_experience_years: rawJob.requirements?.min_experience_years || 0
        },
        basic_info: {
            job_title: rawJob.basic_info?.job_title || "Position",
            company_name: rawJob.basic_info?.company_name || "Unknown Company",
            address: rawJob.basic_info?.address || rawJob.basic_info?.location_city || ""
        }
    };
};

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

const getMatchesForCandidate = async (req, res) => {
    try {
        const candidateId = req.params.candidateId;

        // Fetch Candidate Profile
        const candidateSnap = await db.ref(`candidates/${candidateId}`).once('value');
        if (!candidateSnap.exists()) {
            return res.status(404).json({ error: "Candidate not found." });
        }
        
        const candidateData = candidateSnap.val();
        const personalInfo = candidateData.personal_info || {};
        const maxDist = personalInfo.max_distance || 25; 
        
        const secureCandidatePayload = anonymizeCandidateData(candidateData, candidateId);

        // Fetch All Available Jobs
        const jobsSnap = await db.ref('jobs').once('value');
        const allJobs = jobsSnap.val() || {};
        let matchResults = [];

        // Processing Loop
        for (const rawJobId in allJobs) {
            // Normalize the job structure immediately at the entry point
            const jobData = normalizeJobData(allJobs[rawJobId], rawJobId);
            const jobLoc = jobData.location;

            console.log(`Checking job: ${jobData.basic_info.job_title} | ID: ${jobData.jobId}`);

            // --- FILTER A: Geo-Distance ---
            if (req.body?.lat && jobLoc.lat) { 
                const distance = calculateDistance(req.body.lat, req.body.lng, jobLoc.lat, jobLoc.lng);
                if (distance > maxDist) continue; 
                jobData.calculated_distance = Number(distance.toFixed(1));
            }

            // --- FILTER B: Strict Schedule ---
            if (jobData.availability && candidateData.availability) {
                const scheduleScore = calculateScheduleMatch(jobData.availability, candidateData.availability);
                if (scheduleScore < 100) {
                    console.log(`DEBUG: Job ${jobData.jobId} failed Schedule Match (Score: ${scheduleScore})`);
                    continue; 
                }
            }

            // --- FILTER C: Dealbreakers ---
            if (failsDealbreakers(candidateData.preferences, jobData.characteristics)) {
                console.log(`DEBUG: Job ${jobData.jobId} failed Dealbreakers`);
                continue;
            }

            try {
                // --- STEP D: AI Semantic Scoring ---
                
                // Construct clean payload using normalized fields
                const aiJobPayload = {
                    description: jobData.description,
                    apparel_requirements: jobData.apparel_requirements,
                    requirements: jobData.requirements,
                    basic_info: {
                        location_city: jobData.basic_info.address.split(',').pop().trim(),
                        job_title: jobData.basic_info.job_title
                    },
                    dealbreakers: jobData.dealbreakers
                };

                // Send clean data to Python AI server
                const aiResponse = await getAiSemanticScore(aiJobPayload, secureCandidatePayload);
                
                let rawAiScore = 0;
                let aiExplanation = "Match based on your overall profile and skills.";
                let isHardRejected = false;

                if (aiResponse && typeof aiResponse === 'object') {
                    rawAiScore = aiResponse.Final_Score ?? aiResponse.score ?? 0;
                    aiExplanation = aiResponse.Reason || aiResponse.reason || aiExplanation;
                    if (aiResponse.Status === "REJECTED") {
                        isHardRejected = true;
                    }
                }

                // --- STEP E: Final Decision Processing ---
                if (isHardRejected) {
                    matchResults.push({
                        jobId: jobData.jobId,
                        job_title: jobData.basic_info.job_title,
                        company_name: jobData.basic_info.company_name,
                        final_match_score: 0,
                        match_explanation: aiExplanation, 
                        distance_km: jobData.calculated_distance || 0,
                        status: "REJECTED",
                        breakdown: aiResponse.Breakdown || {},
                        full_job_data: jobData 
                    });
                } else {
                    const finalResult = calculateFinalMatchScore(jobData, candidateData, rawAiScore);

                    if (finalResult.finalScore > 0) {
                        matchResults.push({
                            jobId: jobData.jobId,
                            job_title: jobData.basic_info.job_title,
                            company_name: jobData.basic_info.company_name,
                            final_match_score: finalResult.finalScore,
                            match_explanation: aiExplanation, 
                            distance_km: jobData.calculated_distance || 0,
                            status: finalResult.status,
                            breakdown: finalResult.breakdown,
                            full_job_data: jobData 
                        });
                    }
                }
            } catch (aiError) {
                logger.error(`AI logic error for job ${jobData.jobId}: ${aiError.message}`);
            }
        }

        // Sort matches (Highest score first)
        matchResults.sort((a, b) => b.final_match_score - a.final_match_score);

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