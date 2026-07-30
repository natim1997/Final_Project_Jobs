const { db } = require('../config/firebase');
const { getAiSemanticScore } = require('../services/aiService');
const { calculateFinalMatchScore, estimateDistanceKm } = require('../utils/matchCalculator');
const { calculateScheduleMatch } = require('../utils/scheduleMatcher');
const logger = require('../config/logger');


// ==========================================
// Matchmaking Helper Functions (Adapted for Flat Schema)
// ==========================================

const failsLicenseDealbreaker = (candidateLicenses, jobText) => {
    // check if job requires a license and candidate has one
    const licenseKeywords = ["driver's license", "רישיון נהיגה", "רישיון"];
    const needsLicense = licenseKeywords.some(kw => jobText.toLowerCase().includes(kw));
    const hasLicense = candidateLicenses && candidateLicenses.length > 0;
    
    return needsLicense && !hasLicense;
};

// ==========================================
// Main Controller
// ==========================================

const getMatchesForCandidate = async (req, res) => {
    try {
        const candidateId = req.params.candidateId;
        
        // Get specific job ID from query if triggered by a single job update
        const specificJobId = req.query.jobId; 

        // Fetch Candidate Profile from Firestore
        const candidateDoc = await db.collection('candidates').doc(candidateId).get();
        if (!candidateDoc.exists) {
            return res.status(404).json({ error: "Candidate not found." });
        }
        
        const candidateData = candidateDoc.data();
        
        // We will accumulate matches. If triggered for all jobs, we overwrite. 
        // If triggered for a specific job, we will merge this new match with the existing jobMatches.
        let matchResults = [];

        // ==========================================
        // THE FUNNEL: Fetching All Jobs to Prevent String Bugs
        // ==========================================
        
        // Fetch all jobs from database to avoid strict string matching bugs
        const jobsSnap = await db.collection('jobs').get();
        
        if (jobsSnap.empty) {
            // Clean the array if no jobs exist in the system
            await db.collection('candidates').doc(candidateId).update({ jobMatches: [] });
            return res.status(200).json({
                success: true,
                message: "No jobs found in the system.",
                total_matches: 0,
                matches: [] 
            });
        }

        // Processing Loop for the filtered jobs
        for (const doc of jobsSnap.docs) {
            const jobData = doc.data();
            jobData.id = doc.id; 

            // Skip other jobs if we are only triggered to match a specific new job
            if (specificJobId && jobData.id !== specificJobId) {
                continue;
            }

            // Prevent user from matching with their own job
            if (jobData.employerId === candidateId) {
                console.log(`DEBUG: Skipping job ${jobData.id} - User is the employer`);
                continue;
            }

            // Real city-based distance (haversine over israelCities.js coordinates) -
            // same estimator matchCalculator.js uses for its own location gate later,
            // so the AI's pre-filter and the final gate agree with each other. Only
            // an explicit candidate-supplied distance_to_job overrides it.
            const { distanceKm: estimatedDistance } = estimateDistanceKm(jobData, candidateData);
            const distanceToJob = candidateData.distance_to_job !== undefined
                ? Number(candidateData.distance_to_job)
                : (estimatedDistance !== null ? estimatedDistance : 0);
            const searchRadius = candidateData.searchRadius !== undefined ? Number(candidateData.searchRadius) : 50.0;
            
            console.log(`Checking job: ${jobData.title} | ID: ${jobData.id}`);

            // --- FILTER A: Strict Schedule ---
            const hasCandidateSchedule = candidateData.availableDays && Array.isArray(candidateData.availableDays) && candidateData.availableDays.length > 0;
            
            if (jobData.date && hasCandidateSchedule) {
                const scheduleScore = calculateScheduleMatch(jobData.date, candidateData.availableDays);
                if (scheduleScore < 100) {
                    console.log(`DEBUG: Job ${jobData.id} failed Schedule Match`);
                    continue; 
                }
            }

            // --- FILTER B: License Dealbreaker ---
            const combinedJobText = `${jobData.title} ${jobData.description} ${jobData.requirements}`.toLowerCase();
            if (failsLicenseDealbreaker(candidateData.licenses, combinedJobText)) {
                console.log(`DEBUG: Job ${jobData.id} failed License Dealbreaker`);
                continue;
            }

            try {
                // --- STEP C: AI Semantic Scoring & Payload Mapping ---
                const aiJobPayload = {
                    category: jobData.category,
                    description: jobData.description,
                    // Real, dedicated "must-have" tags (short atomic strings), distinct
                    // from the free-text requirements paragraph below. Doesn't exist in
                    // the job creation form yet, so this is normally undefined/empty -
                    // the Python gatekeeper treats an empty list as "not applicable".
                    criticalRequirements: jobData.criticalRequirements || [],
                    requirements: {
                        languages: [],
                        tech_stack: [],
                        tools: [],
                        min_experience_years: 0,
                        mandatory_skills: typeof jobData.requirements === 'string' ? [jobData.requirements] : jobData.requirements
                    },
                    basic_info: {
                        location_city: jobData.address,
                        job_title: jobData.title
                    },
                    dealbreakers: {
                        requires_license: combinedJobText.includes("רישיון"),
                        is_remote: false,
                        is_student_only: combinedJobText.includes("סטודנט")
                    }
                };

                // The real candidate profile only has a single free-text "skills"
                // string (e.g. "שירות לקוחות, סבלנות, עבודה עם קופה"), not the
                // richer softSkills/jobCatagories arrays this payload used to
                // assume - those were always empty in production, silently
                // killing Model 3's soft-skill signal. Split the string into a
                // pseudo-array so the AI engine still gets real signal from it.
                const candidateSkillsList = typeof candidateData.skills === 'string'
                    ? candidateData.skills.split(',').map(s => s.trim()).filter(Boolean)
                    : (candidateData.softSkills || []);

                const candidateProfileForAi = {
                    // pass 'id' so python logger stops saying 'unknown'
                    id: candidateId,
                    candidateId: candidateId,
                    semantic_profile: candidateData.semantic_profile || candidateData.bio || candidateData.other || "",
                    // pass the correct distance and search radius
                    distance_to_job: distanceToJob,
                    searchRadius: searchRadius,
                    // jobCatagories stays [] in practice - there is no "preferred
                    // category" field on the candidate profile today, so the
                    // category-match bonus (Model 3's 80+/90+ tier) can't fire yet.
                    jobCatagories: candidateData.jobCatagories || [],
                    softSkills: candidateSkillsList,
                    skills: {
                        licenses: candidateData.licenses || [],
                        languages: candidateData.languages || [],
                        tech_stack: candidateData.software || [],
                        tools: candidateData.certificates || []
                    },
                    personal_info: {
                        full_name: candidateData.name || "",
                        city: candidateData.city || candidateData.address || "",
                        is_student: (candidateData.bio || "").includes("סטודנט")
                    }
                };

                const aiResponse = await getAiSemanticScore(aiJobPayload, candidateProfileForAi);
                
                let rawAiScore = 0;
                let aiExplanation = "Match based on your overall profile and skills.";
                let isHardRejected = false;

                if (aiResponse && typeof aiResponse === 'object') {
                    rawAiScore = aiResponse.Final_Score ?? aiResponse.score ?? 0;
                    aiExplanation = aiResponse.Reason || aiResponse.reason || aiExplanation;
                    if (aiResponse.Status === "REJECTED" || aiResponse.Status === "NO MATCH") {
                        // also handle NO MATCH from radius failure
                        if (rawAiScore === 0) {
                            isHardRejected = true;
                        }
                    }
                }

                // --- STEP D: Final Decision Processing ---
                if (!isHardRejected) {
                    const finalResult = calculateFinalMatchScore(jobData, candidateData, rawAiScore);

                    if (finalResult.finalScore > 0) {
                        matchResults.push({
                            jobId: jobData.id,
                            job_title: jobData.title,
                            company_name: jobData.company,
                            final_match_score: finalResult.finalScore,
                            match_explanation: aiExplanation, 
                            status: finalResult.status,
                            breakdown: finalResult.breakdown,
                            full_job_data: jobData 
                        });
                    }
                } else {
                    // log the rejection reason from python
                    console.log(`DEBUG: Job ${jobData.id} was rejected by Python AI: ${aiExplanation}`);
                }
            } catch (aiError) {
                logger.error(`AI logic error for job ${jobData.id}: ${aiError.message}`);
            }
        }

        // ==========================================
        // STEP E: Save matches to Candidate Profile
        // ==========================================
        
        let newJobMatchesToSave = matchResults.map(match => ({
            jobId: match.jobId,
            score: match.final_match_score
        }));

        let finalMatchesToUpdate = [];

        // If we only checked ONE job, we shouldn't delete the old matches. We must merge them.
        if (specificJobId) {
            let existingMatches = candidateData.jobMatches || [];
            
            // Remove the old score for this specific job if it existed
            existingMatches = existingMatches.filter(m => m.jobId !== specificJobId);
            
            // Combine old matches with the newly calculated one
            finalMatchesToUpdate = [...existingMatches, ...newJobMatchesToSave];
        } else {
            // If we checked ALL jobs (no specificJobId), overwrite everything
            finalMatchesToUpdate = newJobMatchesToSave;
        }

        // Sort before saving (Highest score first)
        finalMatchesToUpdate.sort((a, b) => b.score - a.score);

        console.log(`Saving ${finalMatchesToUpdate.length} matches to candidate document...`);

        // Direct document update
        await db.collection('candidates').doc(candidateId).update({
            jobMatches: finalMatchesToUpdate
        });

        res.status(200).json({
            success: true,
            total_matches: finalMatchesToUpdate.length,
            matches: matchResults 
        });

    } catch (error) {
        logger.error("Matchmaking Error:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
};

module.exports = { getMatchesForCandidate };