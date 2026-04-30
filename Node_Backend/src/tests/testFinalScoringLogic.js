const { calculateFinalMatchScore } = require('../utils/matchCalculator');

const runScoringTest = () => {
    console.log("📊 --- FINAL SCORING LOGIC TEST (Fixed) --- 📊\n");

    const scenarios = [
        {
            name: "Scenario 1: The 'Perfect' Candidate (The 99% Trap)",
            aiScore: 99.5,
            job: { requirements: ["React", "Node"], availability: { days: [1, 2], hours: "9-17" } },
            candidate: { skills: ["React", "Node"], availability: { days: [1, 2], hours: "9-17" } }
        },
        {
            name: "Scenario 2: Strong Match but Missing 1 Skill & Partial Schedule",
            aiScore: 88.0,
            job: { requirements: ["React", "Node", "Docker"], availability: { days: [1], hours: "9-17" } },
            candidate: { skills: ["React", "Node"], availability: { days: [1], hours: "10-12" } } // Missing Docker + partial schedule
        },
        {
            name: "Scenario 3: Weak Semantic Match (Borderline)",
            aiScore: 62.0,
            job: { requirements: ["Python"], availability: { days: [5], hours: "8-16" } },
            candidate: { skills: ["Java"], availability: { days: [5], hours: "8-16" } }
        }
    ];

    scenarios.forEach(s => {
        // תיקון סדר הפרמטרים: job, then candidate, then aiScore
        const result = calculateFinalMatchScore(s.job, s.candidate, s.aiScore);
        
        console.log(`🔹 ${s.name}`);
        console.log(`   - Raw AI Score: ${s.aiScore}%`);
        console.log(`   - Final Weighted Score: ${result.finalScore}%`); // שימוש בשם השדה הנכון
        
        if (result.breakdown) {
            console.log(`   - Breakdown: AI(${result.breakdown.aiSemantic}%), Skills(${result.breakdown.skillsMatch}%), Schedule(${result.breakdown.schedule}%)`);
        }
        console.log("------------------------------------------");
    });
};

runScoringTest();