const { db } = require('../config/firebase');
const logger = require('../config/logger');
const pdfParse = require('pdf-parse');
const axios = require('axios');
const { triggerSingleCandidateMatch } = require('../services/backgroundMatcher');

const createCandidate = async (req, res) => {
    try {
        let data = req.body.candidateData ? JSON.parse(req.body.candidateData) : req.body;
        const userId = data.id || (req.user ? req.user.uid : db.collection('candidates').doc().id);
        const candidateRef = db.collection('candidates').doc(userId);

        // Read-before-write so we never wipe fields that aren't part of this request
        const existingDoc = await candidateRef.get();
        const existingData = existingDoc.exists ? existingDoc.data() : {};

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

        let semanticProfile = existingData.semantic_profile || "";
        try {
            const aiServerBase = process.env.AI_SERVER_URL || "http://127.0.0.1:5000";
            const generateBioUrl = `${aiServerBase}/api/generate-bio`;
            console.log("DEBUG: Generating bio via AI at:", generateBioUrl);

            const aiResponse = await axios.post(generateBioUrl, {
                ...data,
                extracted_cv_text: cvText
            });
            semanticProfile = aiResponse.data.generated_bio;
        } catch (aiErr) {
            logger.warn("Python AI not reachable, using fallback text generation");
            semanticProfile = `${data.bio || existingData.bio || ""} ${data.other || existingData.other || ""}`.trim();
        }

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

        await candidateRef.set(updatedData);

        // Awaited (not fire-and-forget) so the match run finishes before the response
        // is sent - see backgroundMatcher.js for why Cloud Run makes that necessary.
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