const { calculateFinalMatchScore } = require('../utils/matchCalculator');

// ==========================================
// Correct Mock Data Format (Matching scheduleMatcher.js)
// ==========================================

const jobs = [
    {
        id: "job_waiter",
        basic_info: { job_title: "Shift Manager - Coffee Shop" },
        requirements: ["Leadership", "Customer Service", "Coffee Making"],
        // Correct structure for scheduleMatcher.js
        availability: { 
            monday: [{ start: "08:00", end: "16:00" }],
            tuesday: [{ start: "08:00", end: "16:00" }],
            wednesday: [{ start: "08:00", end: "16:00" }]
        }
    }
];

const candidates = [
    {
        name: "Yossi (Perfect Fit)",
        skills: ["Leadership", "Customer Service", "Coffee Making"],
        availability: { 
            monday: [{ start: "08:00", end: "16:00" }],
            tuesday: [{ start: "08:00", end: "16:00" }],
            wednesday: [{ start: "08:00", end: "16:00" }]
        },
        mockAiScore: 99.5
    },
    {
        name: "Noa (Schedule Conflict)",
        skills: ["Leadership", "Customer Service", "Coffee Making"],
        availability: { 
            monday: [{ start: "12:00", end: "14:00" }] // Covers only 2 hours out of 8
        },
        mockAiScore: 95
    },
    {
        name: "Amit (Semantic Match / No Skills)",
        skills: [],
        availability: { 
            monday: [{ start: "08:00", end: "16:00" }],
            tuesday: [{ start: "08:00", end: "16:00" }],
            wednesday: [{ start: "08:00", end: "16:00" }]
        },
        mockAiScore: 80
    }
];

// ==========================================
// Execution Logic
// ==========================================

const runTest = () => {
    console.log("🚀 --- FINAL INTEGRATION TEST (STRICT MODE) --- 🚀\n");

    candidates.forEach(can => {
        console.log(`👤 Candidate: ${can.name}`);
        jobs.forEach(job => {
            const result = calculateFinalMatchScore(job, can, can.mockAiScore);
            
            if (result.finalScore === 0) {
                console.log(`   ❌ SKIPPED: Schedule Conflict for ${job.basic_info.job_title}`);
            } else {
                console.log(`   ✅ MATCH: ${result.finalScore}% for ${job.basic_info.job_title}`);
                console.log(`      (Breakdown: AI 60% of ${can.mockAiScore}, Skills 40%)`);
            }
        });
        console.log("------------------------------------------");
    });
};

runTest();