const axios = require('axios');

const getAiSemanticScore = async (job, candidate) => {
    try {
        const pythonServerUrl = 'http://127.0.0.1:5000/api/match'; 

        // Sending the structure exactly as app.py expects
        const payload = {
            job: job,
            candidate: candidate
        };

        const response = await axios.post(pythonServerUrl, payload);

        // Your Python script returns "Final_Score"
        return response.data.Final_Score || 0;

    } catch (error) {
        console.error("Error communicating with Python AI Server:", error.message);
        return 50; 
    }
};

module.exports = { getAiSemanticScore };