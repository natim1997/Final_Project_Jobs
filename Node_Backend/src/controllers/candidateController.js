const { db } = require('../config/firebase');

/**
 * Saves or updates a candidate profile in the Firebase Realtime Database.
 * @param {Object} req - The HTTP request object from the Android app
 * @param {Object} res - The HTTP response object
 */
const saveCandidate = async (req, res) => {
    try {
        // In a real app, candidateId comes from Firebase Auth token.
        // For now, we expect the app to send it in the JSON body.
        const candidateId = req.body.candidateId; 
        const candidateData = req.body.candidate;

        if (!candidateId || !candidateData) {
            return res.status(400).json({ 
                error: "Invalid request. Missing 'candidateId' or 'candidate' object." 
            });
        }

        // Save the data to Firebase under the 'candidates' node
        await db.ref(`candidates/${candidateId}`).set(candidateData);

        res.status(200).json({ 
            status: "success",
            message: "Candidate profile saved successfully to Firebase!" 
        });

    } catch (error) {
        console.error(" Error saving candidate to Firebase:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
};

module.exports = { saveCandidate };