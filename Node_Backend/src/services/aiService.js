const axios = require('axios');

const getAiSemanticScore = async (job, candidate) => {
    try {
        // Simple english comment: Use cloud URL from environment variables, fallback to local for development
        const pythonServerUrl = process.env.AI_SERVER_URL 
            ? `${process.env.AI_SERVER_URL}/api/match` 
            : 'http://127.0.0.1:5000/api/match'; 

        // Extract the bio text safely no matter how it is named in Firebase
        const candidateText = candidate.bio || candidate.description || "";

        // Construct the payload and force both naming conventions for safety
        const payload = {
            job: job,
            candidate: {
                ...candidate,
                bio: candidateText,
                description: candidateText
            }
        };

        const response = await axios.post(pythonServerUrl, payload);

        // Safely extract names for the log
        const jobTitle = job.basic_info?.job_title || "Unknown Position";
        const candId = candidate.candidateId || "Unknown Candidate";

        // CRITICAL: Using backticks (`) for string interpolation, NOT quotes (")
        console.log(`\n---- PYTHON AI SCORE FOR: ${jobTitle} | CANDIDATE: ${candId} ----`);
        console.log(response.data);
        console.log("--------------------------------------------------------------\n");

        // Handle Python's Capitalized Keys safely
        let score = response.data.Final_Score ?? response.data.final_score ?? response.data.score ?? 0;
        
        // Scale Fix: Convert decimal to percentage
        if (score > 0 && score <= 1) {
            score = score * 100;
        }
        
        const reason = response.data.Reason || response.data.reason || response.data.explanation || "Match based on your overall profile and skills.";

        return { score, reason };

    } catch (error) {
        console.error("Error communicating with Python AI Server:", error.message);
        return { score: 0, reason: "AI server error fallback." }; 
    }
};

module.exports = { getAiSemanticScore };