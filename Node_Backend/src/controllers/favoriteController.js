const { db } = require('../config/firebase');

/**
 * Adds a job to the candidate's favorites list.
 */
const addFavorite = async (req, res) => {
    try {
        const { candidateId, jobId } = req.body;

        if (!candidateId || !jobId) {
            return res.status(400).json({ error: "Missing 'candidateId' or 'jobId'." });
        }

        // Set the value to 'true' under the specific jobId
        await db.ref(`candidates/${candidateId}/favorites/${jobId}`).set(true);

        res.status(200).json({ 
            status: "success", 
            message: `Job ${jobId} successfully added to favorites!` 
        });

    } catch (error) {
        console.error(" Error adding favorite:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
};

/**
 * Removes a job from the candidate's favorites list.
 */
const removeFavorite = async (req, res) => {
    try {
        const { candidateId, jobId } = req.body;

        if (!candidateId || !jobId) {
            return res.status(400).json({ error: "Missing 'candidateId' or 'jobId'." });
        }

        // Remove the specific node from Firebase
        await db.ref(`candidates/${candidateId}/favorites/${jobId}`).remove();

        res.status(200).json({ 
            status: "success", 
            message: `Job ${jobId} successfully removed from favorites!` 
        });

    } catch (error) {
        console.error(" Error removing favorite:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
};

module.exports = { addFavorite, removeFavorite };