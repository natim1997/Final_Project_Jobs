const { db } = require('../config/firebase');
const logger = require('../config/logger');
const pdfParse = require('pdf-parse');
const axios = require('axios');
const { triggerSingleCandidateMatch } = require('../services/backgroundMatcher');

const createCandidate = async (req, res) => {
    try {
        // 1. Parse incoming data first to extract the frontend ID
        let data = req.body.candidateData ? JSON.parse(req.body.candidateData) : req.body;

        // 2. Use the ID from the frontend, or auth, or generate a new one
        const userId = data.id || (req.user ? req.user.uid : db.collection('candidates').doc().id);

        // 3. Point to the exact document ID in Firestore
        const candidateRef = db.collection('candidates').doc(userId);

        // 4. Fetch existing data first (read-before-write) so we never wipe fields
        //    that aren't part of this specific request.
        const existingDoc = await candidateRef.get();
        const existingData = existingDoc.exists ? existingDoc.data() : {};

        // 5. Extract Text from CV if provided
        let cvText = "";
        if (req.file) {
            try {
                const pdfData = await pdfParse(req.file.buffer);
                cvText = pdfData.text.replace(/\s+/g, ' ').trim();
                console.log("--> DEBUG PDF EXTRACTION: ", cvText.substring(0, 100)); 
            } catch (err) {
                logger.error("Failed to parse PDF text");
            }
        }

        // 6. Request AI Bio Generation from Python
        let semanticProfile = existingData.semantic_profile || "";
        try {
            // Forcing local server instead of process.env.AI_SERVER_URL
            const localAiUrl = "http://127.0.0.1:5000/api/generate-bio";
            console.log("DEBUG: Generating bio via local AI at:", localAiUrl);
            
            const aiResponse = await axios.post(localAiUrl, {
                ...data,
                extracted_cv_text: cvText
            });
            semanticProfile = aiResponse.data.generated_bio;
        } catch (aiErr) {
            logger.warn("Python AI not reachable, using fallback text generation");
            semanticProfile = `${data.bio || existingData.bio || ""} ${data.other || existingData.other || ""}`.trim();
        }

        // 7. Build the merged object.
        const updatedData = {
            ...existingData,
            ...data,

            id: userId,
            semantic_profile: semanticProfile,
            cvName: data.cvName || (req.file ? req.file.originalname : existingData.cvName || ""),

            // Server-owned fields: never trust client input for these
            jobMatches: existingData.jobMatches || [],
            rating: existingData.rating ?? 0,
            ratingsCount: existingData.ratingsCount ?? 0,

            // Keep original creation timestamp if it exists, otherwise set it now
            createdAt: existingData.createdAt || Date.now(),
            updatedAt: Date.now()
        };

        // 8. Save back to Firestore
        await candidateRef.set(updatedData);

        // 9. Run the match engine and WAIT for it to finish before responding.
        if (typeof triggerSingleCandidateMatch === 'function') {
            try {
                await triggerSingleCandidateMatch(userId);
            } catch (matchErr) {
                logger.error(`Match engine failed for candidate ${userId}: ${matchErr.message}`);
            }
        }

        return res.status(200).json({
            message: "Candidate created/updated successfully with AI profile",
            candidateId: userId
        });

    } catch (error) {
        logger.error(`Error in createCandidate: ${error.message}`);
        return res.status(500).json({ error: "Internal server error" });
    }
};
module.exports = { createCandidate };