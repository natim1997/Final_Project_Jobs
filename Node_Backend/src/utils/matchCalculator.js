const { calculateScheduleMatch } = require('./scheduleMatcher');

/**
 * Weighted Score Calculator adapted for dynamic weighting.
 * Handles both technical jobs (skills matching) and general jobs (100% semantic matching).
 */
const calculateFinalMatchScore = (job, candidate, aiSemanticScore) => {
    
    // 1. Strict Schedule Filter
    let scheduleScore = 100;
    if (job.availability && candidate.availability) {
        scheduleScore = calculateScheduleMatch(job.availability, candidate.availability);
    }
    if (scheduleScore < 100) return { finalScore: 0, status: "REJECTED_SCHEDULE" };

    // 2. Extract and combine grouped skills chips into a single flat array
    const candidateSkills = [
        ...(candidate.skills?.tech_stack || []),
        ...(candidate.skills?.tools || []),
        ...(candidate.skills?.certifications || []),
        ...(candidate.skills?.languages || [])
    ];
    
    // Combine job requirements keywords
    const jobKeywords = [
        ...(job.requirements?.tech_stack || []),
        ...(job.requirements?.tools || []),
        ...(job.requirements?.certifications || []),
        ...(job.requirements?.keywords || [])
    ];

    let skillScore = 0;
    let finalAiWeight = 0.6;
    let finalSkillsWeight = 0.4;

    // 3. Dynamic Weighting Logic
    if (jobKeywords.length > 0) {
        // Job requires specific skills -> apply 60/40 split
        const matched = jobKeywords.filter(kw => 
            candidateSkills.some(s => String(s).toLowerCase().includes(String(kw).toLowerCase()))
        );
        skillScore = (matched.length / jobKeywords.length) * 100;
    } else {
        // Job has no technical keywords (e.g., general labor/waiter) 
        // -> AI semantic score dictates 100% of the match
        skillScore = 0;
        finalAiWeight = 1.0;
        finalSkillsWeight = 0.0;
    }

    // 4. Final Weighting Calculation
    let finalScore = (aiSemanticScore * finalAiWeight) + (skillScore * finalSkillsWeight);
    finalScore = Math.round(finalScore);

    // Cap the score at 98 for realism
    if (finalScore > 98) finalScore = 98;

    // Determine Status based on final score
    let matchStatus = "NO MATCH";
    if (finalScore >= 75) {
        matchStatus = "MATCH";
    } else if (finalScore >= 40) {
        matchStatus = "POTENTIAL";
    }

    return {
        finalScore: finalScore,
        status: matchStatus,
        breakdown: {
            aiSemanticWeight: Math.round(aiSemanticScore * finalAiWeight),
            skillsWeight: Math.round(skillScore * finalSkillsWeight)
        }
    };
};

module.exports = { calculateFinalMatchScore };