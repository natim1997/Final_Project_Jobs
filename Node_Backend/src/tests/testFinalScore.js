const { calculateFinalMatchScore } = require('../utils/matchCalculator');

// Mock data: A Job
const job = {
    requirements: ["Node.js", "React", "MongoDB"],
    availability: {
        sunday: [{ start: "08:00", end: "14:00" }],
        is_flexible: true
    }
};

// Mock data: A Great Candidate (Almost Perfect)
const candidate1 = {
    skills: ["Node.js", "React", "MongoDB", "Python"], // Extra skill
    availability: {
        sunday: [{ start: "08:00", end: "14:00" }],
        is_flexible: true
    }
};

// Simulation: The Python server gave this candidate a 99% semantic score
const pythonAiScore = 99;

console.log("\n🚀 Testing Final Equation...");

const result = calculateFinalMatchScore(job, candidate1, pythonAiScore);

console.log(`\n--- RESULT ---`);
console.log(`🛠️ Skills Match:   ${result.breakdown.skillsMatch}%`);
console.log(`🧠 AI Semantic:    ${result.breakdown.aiSemantic}%`);
console.log(`🕒 Schedule Match: ${result.breakdown.schedule}%`);
console.log(`=========================`);
console.log(`🏆 FINAL SCORE:    ${result.finalScore}%`);
console.log("\n");