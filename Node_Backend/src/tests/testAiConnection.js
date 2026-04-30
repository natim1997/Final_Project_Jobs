const { getAiSemanticScore } = require('../services/aiService');

// This matches the structure in your final_pipeline.py
const mockJob = {
    text_fields: {
        title: "Software Engineer",
        description: "Experienced developer for full stack position with React and Node.js"
    },
    requirements: {
        required_hard_skills: ["React", "Node.js", "MongoDB"],
        required_languages: ["English"],
        min_experience_years: 2
    },
    basic_info: {
        location_city: "Tel Aviv",
        work_model: "Hybrid"
    }
};

const mockCandidate = {
    text_fields: {
        bio: "Full stack developer with 3 years of experience in React and Node.js. Love MongoDB."
    },
    experience_and_skills: {
        hard_skills: ["React", "Node.js", "JavaScript", "MongoDB"],
        languages: ["English", "Hebrew"],
        total_experience_years: 3
    },
    personal_info: {
        location_city: "Tel Aviv",
        education_level: "B.Sc Computer Science"
    },
    availability_and_schedule: {
        work_model_preference: "Hybrid"
    }
};

const runTest = async () => {
    console.log("🚀 Sending Structured Data to AI Pipeline...");
    const score = await getAiSemanticScore(mockJob, mockCandidate);
    console.log(`🧠 AI Semantic Match Result: ${score}%`);
};

runTest();