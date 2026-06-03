const { db } = require('../config/firebase');

/**
 * Saves or updates a candidate profile based on the new wizard design.
 * Handles grouped skills chips, structured experience, and dynamic semantic profile for AI.
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

        // simple english comment: Build the dynamic semantic profile for the AI model
        let semanticParts = [];

        // Add bio if exists
        if (candidateData.bio) {
            semanticParts.push(`About the candidate: ${candidateData.bio}`);
        }

        // Add skills if they exist
        let skillsText = [];
        if (candidateData.skills?.languages?.length) skillsText.push(`Languages: ${candidateData.skills.languages.join(', ')}`);
        if (candidateData.skills?.licenses?.length) skillsText.push(`Licenses: ${candidateData.skills.licenses.join(', ')}`);
        if (candidateData.skills?.tools?.length) skillsText.push(`Tools: ${candidateData.skills.tools.join(', ')}`);
        if (candidateData.skills?.tech_stack?.length) skillsText.push(`Tech Stack: ${candidateData.skills.tech_stack.join(', ')}`);
        if (candidateData.skills?.certifications?.length) skillsText.push(`Certifications: ${candidateData.skills.certifications.join(', ')}`);
        
        if (skillsText.length > 0) {
            semanticParts.push(`Skills: ${skillsText.join('. ')}`);
        }

        // Add extracted CV text OR manual experience
        if (candidateData.cv_extracted_text) {
            semanticParts.push(`Professional Experience and Resume: ${candidateData.cv_extracted_text}`);
        } else if (candidateData.experience && candidateData.experience.length > 0) {
            // fallback if they entered experience manually
            const expArray = candidateData.experience.map(exp => `${exp.role} (${exp.years} years)`);
            semanticParts.push(`Experience: ${expArray.join(', ')}`);
        }

        // Combine everything into one rich text string
        const full_semantic_profile = semanticParts.join(' | ');

        // simple english comment: Map incoming fields to the new flexible wizard schema
        const updatedProfile = {
            personal_info: {
                full_name: candidateData.personal_info?.full_name || "Unknown",
                phone: candidateData.personal_info?.phone || "",
                email: candidateData.personal_info?.email || "",
                city: candidateData.personal_info?.city || "",
                max_distance: candidateData.personal_info?.max_distance || 15
            },
            availability: candidateData.availability || { is_always_available: true },
            skills: {
                languages: candidateData.skills?.languages || [],
                licenses: candidateData.skills?.licenses || [],
                tools: candidateData.skills?.tools || [],
                tech_stack: candidateData.skills?.tech_stack || [],
                certifications: candidateData.skills?.certifications || []
            },
            experience: candidateData.experience || [], 
            bio: candidateData.bio || "",
            cv_url: candidateData.cv_url || null,
            cv_extracted_text: candidateData.cv_extracted_text || null,
            full_semantic_profile: full_semantic_profile, // The complete text chunk for RoBERTa
            updated_at: Date.now()
        };

        // simple english comment: Save the structured data to Firebase under the candidates node
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