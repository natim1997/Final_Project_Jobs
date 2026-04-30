const { calculateScheduleMatch } = require('./scheduleMatcher');

/**
 * FINAL CALCULATOR - Optimized for your Firebase structure
 */
const calculateFinalMatchScore = (job, candidate, aiSemanticScore) => {
    
    // 1. Strict Schedule Filter
    let scheduleScore = 100;
    if (job.availability && candidate.availability) {
        scheduleScore = calculateScheduleMatch(job.availability, candidate.availability);
    }
    if (scheduleScore < 100) return { finalScore: 0, status: "REJECTED_SCHEDULE" };

    // 2. Hard Skills (Mapping to your DB: experience_and_skills -> hard_skills)
    let skillScore = 0;
    const candidateSkillsObj = candidate.experience_and_skills?.hard_skills || {};
    // Convert object keys { "Python": true } to array ["Python"]
    const candidateSkills = Object.keys(candidateSkillsObj); 
    
    const jobKeywords = job.requirements?.keywords || [];

    if (jobKeywords.length > 0) {
        const matched = jobKeywords.filter(kw => 
            candidateSkills.some(s => s.toLowerCase().includes(kw.toLowerCase()))
        );
        skillScore = (matched.length / jobKeywords.length) * 100;
    } else {
        skillScore = 100;
    }

    // 3. Final Weighting (60% AI / 40% Skills)
    let finalScore = (aiSemanticScore * 0.6) + (skillScore * 0.4);
    finalScore = Math.round(finalScore);

    // 4. Reality Check (98% Cap)
    if (finalScore > 98) finalScore = 98;

    return {
        finalScore: finalScore,
        status: finalScore >= 75 ? "MATCH" : "POTENTIAL",
        breakdown: {
            aiSemanticWeight: Math.round(aiSemanticScore * 0.6),
            skillsWeight: Math.round(skillScore * 0.4)
        }
    };
};

module.exports = { calculateFinalMatchScore };