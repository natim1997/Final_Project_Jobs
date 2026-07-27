const axios = require('axios');

const getAiSemanticScore = async (job, candidate) => {
    try {
        // simple english comment: LOCAL TESTING URL - Using local server for testing the new AI model
        const pythonServerUrl = "http://127.0.0.1:5000/api/match";

        // simple english comment: CLOUD URL - Commented out for local testing
        // const pythonServerUrl = "https://clickjob-ai-engine-493713788422.europe-west1.run.app/api/match";

        // simple english comment: Extract the bio text safely no matter how it is named in Firebase
        const candidateText = candidate.bio || candidate.description || "";

        // simple english comment: Construct the payload and force both naming conventions for safety
        const payload = {
            job: job,
            candidate: {
                ...candidate,
                bio: candidateText,
                description: candidateText
            }
        };

        const response = await axios.post(pythonServerUrl, payload);

        // simple english comment: Safely extract names for the log
        const jobTitle = job.basic_info?.job_title || "Unknown Position";
        const candId = candidate.candidateId || "Unknown Candidate";

        // simple english comment: CRITICAL: Using backticks (`) for string interpolation, NOT quotes (")
        console.log(`\n---- PYTHON AI SCORE FOR: ${jobTitle} | CANDIDATE: ${candId} ----`);
        console.log(response.data);
        console.log("--------------------------------------------------------------\n");

        // simple english comment: Handle Python's Capitalized Keys safely
        let score = response.data.Final_Score ?? response.data.final_score ?? response.data.score ?? 0;

        // simple english comment: Scale Fix: Convert decimal to percentage
        if (score > 0 && score <= 1) {
            score = score * 100;
        }

        const reason = response.data.Reason || response.data.reason || response.data.explanation || "Match based on your overall profile and skills.";
        const status = response.data.Status || response.data.status || "NO MATCH";

        // simple english comment: Return both naming formats to ensure matchController.js catches it
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