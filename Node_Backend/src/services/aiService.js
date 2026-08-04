const axios = require('axios');

const getAiSemanticScore = async (job, candidate) => {
    try {
        // AI_SERVER_URL comes from the environment (set in .env locally, or as
        // a Cloud Run env var in production) - falls back to localhost only
        // for convenience when no env var is set.
        const aiServerBase = process.env.AI_SERVER_URL || "http://127.0.0.1:5000";
        const pythonServerUrl = `${aiServerBase}/api/match`;

        // Candidate profile field is named inconsistently across callers (bio vs description)
        const candidateText = candidate.bio || candidate.description || "";

        // Send both field names so the AI engine finds the text regardless of which it reads
        const payload = {
            job: job,
            candidate: {
                ...candidate,
                bio: candidateText,
                description: candidateText
            }
        };

        const response = await axios.post(pythonServerUrl, payload);

        const jobTitle = job.basic_info?.job_title || "Unknown Position";
        const candId = candidate.candidateId || "Unknown Candidate";

        console.log(`\n---- PYTHON AI SCORE FOR: ${jobTitle} | CANDIDATE: ${candId} ----`);
        console.log(response.data);
        console.log("--------------------------------------------------------------\n");

        // Python's response uses Capitalized keys; check lowercase too in case that changes
        let score = response.data.Final_Score ?? response.data.final_score ?? response.data.score ?? 0;

        // Older AI responses returned a 0-1 decimal instead of a 0-100 score
        if (score > 0 && score <= 1) {
            score = score * 100;
        }

        const reason = response.data.Reason || response.data.reason || response.data.explanation || "Match based on your overall profile and skills.";
        const status = response.data.Status || response.data.status || "NO MATCH";

        // Both naming conventions returned since matchController.js reads Final_Score/score interchangeably
        return {
            score: score,
            reason: reason,
            Final_Score: score,
            Reason: reason,
            Status: status
        };

    } catch (error) {
        console.error("Error communicating with Python AI Server:", error.message);
        return {
            score: 0,
            reason: "AI server error fallback.",
            Final_Score: 0,
            Status: "NO MATCH"
        };
    }
};

module.exports = { getAiSemanticScore };