// Import the matching logic we just created
const { calculateScheduleMatch } = require('./utils/scheduleMatcher');

// --- Define the Job's Required Schedule ---
const jobSchedule = {
    sunday: [{ start: "08:00", end: "14:00" }],     // Requires 6 hours
    monday: [{ start: "16:00", end: "22:00" }],     // Requires 6 hours
    tuesday: [],
    wednesday: [{ start: "10:00", end: "15:00" }],  // Requires 5 hours
    thursday: [],
    friday: [],
    saturday: [],
    is_flexible: false                              // Employer is strict
};

// --- Define the Candidate's Available Schedule ---
const candidateSchedule = {
    sunday: [{ start: "09:00", end: "15:00" }],     // Overlaps from 09:00 to 14:00 (Misses 1 morning hour)
    monday: [{ start: "15:00", end: "20:00" }],     // Overlaps from 16:00 to 20:00 (Misses 2 evening hours)
    tuesday: [{ start: "08:00", end: "20:00" }],    // Free, but not needed by the job
    wednesday: [{ start: "10:00", end: "15:00" }],  // Perfect match for Wednesday
    thursday: [],
    friday: [],
    saturday: [],
    is_flexible: false                               // Candidate is willing to adjust
};

// --- Run the Simulation ---
console.log("\n🚀 Testing Schedule Matcher Algorithm...\n");

const score = calculateScheduleMatch(jobSchedule, candidateSchedule);

console.log(`📊 FINAL SCHEDULE MATCH SCORE: ${score}%`);

if (score >= 80) {
    console.log("✅ Excellent Time Match! The schedules align perfectly.");
} else if (score >= 50) {
    console.log("⚠️ Partial Time Match. Might work with minor adjustments.");
} else {
    console.log("❌ Poor Time Match. Schedules collide.");
}
console.log("\n");