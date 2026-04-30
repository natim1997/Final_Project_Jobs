// --- נתונים מפורטים: משרות ---
const jobs = [
    { id: "J1", title: "Full Stack Dev", requirements: ["Node.js", "React", "MongoDB", "Git"] },
    { id: "J2", title: "Cyber Analyst", requirements: ["Network Security", "Python", "Linux"] },
    { id: "J3", title: "Cafe Waiter", requirements: ["Customer Service", "Teamwork", "Fast-paced environment"] },
    { id: "J4", title: "Truck Driver", requirements: ["C1 License", "Driving Experience", "Physical Fitness"] },
    { id: "J5", title: "Retail Store", requirements: ["Sales", "Customer Service", "Organization"] }
];

// --- נתונים מפורטים: מועמדים ---
const candidates = [
    { id: "C1", name: "Arad (Tech)", skills: ["React", "Node.js", "JavaScript", "MongoDB", "Git"] },
    { id: "C2", name: "Dana (Cyber)", skills: ["Python", "Linux", "Network Security", "Bash"] },
    { id: "C3", name: "Yossi (Service)", skills: ["Customer Service", "Teamwork", "Sales", "Fast-paced environment"] },
    { id: "C4", name: "Avi (Driver)", skills: ["C1 License", "Driving Experience", "Logistics", "Physical Fitness"] }
];

// --- מטריצת ההתאמות של ה-AI ---
const aiMatrix = {
    "C1": { "J1": 95, "J2": 25, "J3": 35, "J4": 10, "J5": 20 }, // ארד (הייטק)
    "C2": { "J1": 30, "J2": 92, "J3": 20, "J4": 15, "J5": 20 }, // דנה (סייבר)
    "C3": { "J1": 10, "J2": 15, "J3": 95, "J4": 20, "J5": 88 }, // יוסי (שירות ומכירות)
    "C4": { "J1":  5, "J2": 10, "J3": 20, "J4": 98, "J5": 30 }  // אבי (נהיגה ולוגיסטיקה)
};

// --- הרצת הרשימה ---
console.log("\n🚀 Starting Matchmaker List Simulation...\n");

// לולאה שעוברת על כל מועמד
candidates.forEach(candidate => {
    console.log(`======================================================`);
    console.log(`🧑‍🎓 CANDIDATE: ${candidate.name}`);
    console.log(`======================================================`);
    
    // לכל מועמד, עוברים על כל המשרות
    jobs.forEach(job => {
        // 1. חישוב חפיפת מילות מפתח
        const matchedSkills = job.requirements.filter(req => candidate.skills.includes(req));
        const skillScore = (matchedSkills.length / job.requirements.length) * 100;
        
        // 2. ציון סמנטי
        const semanticScore = aiMatrix[candidate.id][job.id];

        // 3. ציון סופי
        const finalScore = Math.round((skillScore * 0.4) + (semanticScore * 0.6));
        
        // קביעת חיווי ויזואלי
        let verdict = "";
        if (finalScore >= 75) verdict = "✅ EXCELLENT";
        else if (finalScore >= 50) verdict = "⚠️ PARTIAL  ";
        else verdict = "❌ POOR     ";

        // הדפסת שורת סיכום למשרה
        console.log(`  🏢 Job: ${job.title.padEnd(16)} | Final Score: ${finalScore.toString().padEnd(3)}% | ${verdict}`);
    });
    
    console.log("\n"); // רווח בין מועמד למועמד לנוחות קריאה
});