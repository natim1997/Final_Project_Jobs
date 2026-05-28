const { db } = require('../config/firebase');

/**
 * Saves or updates a candidate profile based on the new wizard design.
 * Handles grouped skills chips and structured experience array.
 */
const saveCandidate = async (req, res) => {
    try {
        const candidateId = req.body.candidateId; 
        const candidateData = req.body.candidate;

        if (!candidateId || !candidateData) {
            return res.status(400).json({ 
                error: "Invalid request. Missing 'candidateId' or 'candidate' object." 
            });
        }

        // Map incoming fields to the new flexible wizard schema
        // This prevents crashes if optional fields are omitted or skipped
        const updatedProfile = {
            personal_info: {
                full_name: candidateData.personal_info?.full_name || "Unknown",
                phone: candidateData.personal_info?.phone || "",
                email: candidateData.personal_info?.email || "",
                city: candidateData.personal_info?.city || "",
                max_distance: candidateData.personal_info?.max_distance || 15
            },
            // Handle skipped schedule selection (default to always available)
            availability: candidateData.availability || { is_always_available: true },
            skills: {
                languages: candidateData.skills?.languages || [],
                licenses: candidateData.skills?.licenses || [],
                tools: candidateData.skills?.tools || [],
                tech_stack: candidateData.skills?.tech_stack || [],
                certifications: candidateData.skills?.certifications || []
            },
            // Structured array of objects: [{ role: "Waiter", years: 3 }]
            experience: candidateData.experience || [], 
            bio: candidateData.bio || "",
            cv_url: candidateData.cv_url || null,
            updated_at: Date.now()
        };

        // Save the structured data to Firebase under the candidates node
        await db.ref(`candidates/${candidateId}`).set(updatedProfile);

        res.status(200).json({ 
            status: "success",
            message: "Candidate profile saved successfully to Firebase!" 
        });

    } catch (error) {
        console.error("Error saving candidate to Firebase:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
};

module.exports = { saveCandidate };