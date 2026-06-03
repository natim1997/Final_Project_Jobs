const { db } = require('../config/firebase');
const { getAiSemanticScore } = require('../services/aiService');
const { calculateFinalMatchScore } = require('../utils/matchCalculator');
const { calculateScheduleMatch } = require('../utils/scheduleMatcher');
const logger = require('../config/logger');

// ==========================================
// Matchmaking Helper Functions & Normalization
// ==========================================

/**
 * Normalizes raw job data from Firebase into a strict structured object.
 */
const normalizeJobData = (rawJob, jobId) => {
    const description = rawJob.description || rawJob.text_fields?.description || "";
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
            mandatory_skills: rawJob.requirements?.mandatory_skills || [], // New field for hard requirements
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

/**
 * simple english comment: Checks if the job has mandatory skills/certifications that the candidate is missing.
 */
const failsMandatoryRequirements = (candidateSkills, jobRequirements) => {
    if (jobRequirements && jobRequirements.mandatory_skills && jobRequirements.mandatory_skills.length > 0) {
        // Collect all candidate skills into one flat array for easy checking
        const candidateAllSkills = [
            ...(candidateSkills?.languages || []),
            ...(candidateSkills?.tools || []),
            ...(candidateSkills?.tech_stack || []),
            ...(candidateSkills?.certifications || []),
            ...(candidateSkills?.licenses || [])
        ].map(s => s.toLowerCase().trim());

        // Check if every mandatory requirement exists in the candidate's skills
        for (const reqSkill of jobRequirements.mandatory_skills) {
            if (!candidateAllSkills.includes(reqSkill.toLowerCase().trim())) {
                return true; // Failed a mandatory requirement
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
        const maxDist = personalInfo.max_distance || 15; // Defaults to 15km if not set
        
        // Fetch All Available Jobs
        const jobsSnap = await db.ref('jobs').once('value');
        const allJobs = jobsSnap.val() || {};
        let matchResults = [];

        // Processing Loop
        for (const rawJobId in allJobs) {
            const jobData = normalizeJobData(allJobs[rawJobId], rawJobId);
            const jobLoc = jobData.location;

            console.log(`Checking job: ${jobData.basic_info.job_title} | ID: ${jobData.jobId}`);

            // --- FILTER A: Geo-Distance ---
            // simple english comment: Uses request coordinates or falls back to candidate profile coordinates
            const candidateLat = req.body?.lat || personalInfo?.lat;
            const candidateLng = req.body?.lng || personalInfo?.lng;
            
            if (candidateLat && candidateLng && jobLoc.lat && jobLoc.lng) { 
                const distance = calculateDistance(candidateLat, candidateLng, jobLoc.lat, jobLoc.lng);
                if (distance > maxDist) {
                    console.log(`DEBUG: Job ${jobData.jobId} failed Distance (Distance: ${distance.toFixed(1)}km, Max: ${maxDist}km)`);
                    continue; 
                }
                jobData.calculated_distance = Number(distance.toFixed(1));
            } else {
                jobData.calculated_distance = 0; // Fallback if no coordinates exist
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

            // --- FILTER D: Mandatory Requirements (Certifications/Licenses) ---
            if (failsMandatoryRequirements(candidateData.skills, jobData.requirements)) {
                console.log(`DEBUG: Job ${jobData.jobId} failed Mandatory Requirements`);
                continue;
            }

            try {
                // --- STEP E: AI Semantic Scoring ---
                
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

                // simple english comment: Send the dynamic semantic profile we generated earlier!
                const candidateProfileForAi = {
                    candidateId: candidateId,
                    semantic_profile: candidateData.full_semantic_profile || candidateData.bio || "No detailed profile provided.",
                };

                // Send clean data to Python AI server
                const aiResponse = await getAiSemanticScore(aiJobPayload, candidateProfileForAi);
                
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

                // --- STEP F: Final Decision Processing ---
                if (!isHardRejected) {
                    const finalResult = calculateFinalMatchScore(jobData, candidateData, rawAiScore);

                    if (finalResult.finalScore > 0) {
                        matchResults.push({
                            jobId: jobData.jobId,
                            job_title: jobData.basic_info.job_title,
                            company_name: jobData.basic_info.company_name,
                            final_match_score: finalResult.finalScore,
                            match_explanation: aiExplanation, 
                            distance_km: jobData.calculated_distance,
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