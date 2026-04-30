const { db } = require('../config/firebase');

// ==========================================
// The "Clean & Reset" Function
// ==========================================
const resetDatabase = async () => {
    try {
        console.log("🧹 Starting database cleanup...");
        
        // 1. Delete everything in candidates and jobs
        await db.ref('candidates').remove();
        await db.ref('jobs').remove();
        
        console.log("✨ Database cleared. Inserting gold-standard data...");

        // 2. Insert one perfect Candidate (The "Gold" Candidate)
       const sampleCandidate = {
    personal_info: {
        full_name: "Test Student",
        email: "test@student.com",
        phone: "050-0000000"
    },
    location: {
        address: "Tel Aviv, Israel",
        lat: 32.0853,
        lng: 34.7818,
        max_distance_km: 500 // 👈 הגדלנו ל-500 ק"מ כדי לכסות את כל הארץ
    },
    availability: {
        is_flexible: true, // 👈 הפכנו לגמיש כדי לעקוף את מסננת השעות
        monday: [{ start: "00:00", end: "23:59" }],
        tuesday: [{ start: "00:00", end: "23:59" }]
    },
    experience_and_skills: {
        total_experience_years: 1,
        hard_skills: {
            "Office": true, // 👈 הוספתי כישורים נפוצים שהסורק מחפש
            "Service": true
        }
    },
    preferences: {
        // 👈 ביטלנו את ה-Dealbreaker זמנית כדי לראות את כל המשרות
        suitable_for_students: { requested: true, is_dealbreaker: false } 
    },
    text_fields: {
        bio: "I am a student looking for any job opportunity."
    }
};
        // 3. Insert one perfect Job (The "Gold" Job)
        const sampleJob = {
            basic_info: {
                job_title: "Customer Support Specialist",
                company_name: "TechHouse",
                location_city: "Tel Aviv"
            },
            location: {
                lat: 32.0853,
                lng: 34.7818
            },
            availability: {
                monday: [{ start: "08:00", end: "16:00" }],
                tuesday: [{ start: "08:00", end: "16:00" }]
            },
            requirements: {
                min_experience_years: 0,
                keywords: ["Customer Service", "English"]
            },
            characteristics: {
                suitable_for_students: true,
                work_alone: false
            },
            text_fields: {
                description: "We are looking for a student to join our support team in Tel Aviv."
            }
        };

        // Saving to Firebase
        await db.ref('candidates/cand123').set(sampleCandidate);
        await db.ref('jobs/job456').set(sampleJob);

        console.log("🚀 Database is ready! You have 1 clean Candidate and 1 clean Job.");
        process.exit(0);
    } catch (error) {
        console.error("❌ Reset failed:", error);
        process.exit(1);
    }
};

resetDatabase();