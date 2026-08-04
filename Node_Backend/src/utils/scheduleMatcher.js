/**
 * Checks if the job's date matches the candidate's available days.
 * Returns 100 if it's a match (or if candidate is always available).
 * Returns 0 if the candidate is not available on the job's day.
 */
const calculateScheduleMatch = (job, candidate) => {
    // Accepts either the full candidate object or just the availableDays array directly
    const availableDays = candidate.availableDays || candidate || [];

    // Empty/missing means available every day
    if (!Array.isArray(availableDays) || availableDays.length === 0) {
        return 100;
    }

    // Accepts either the full job object or just the date field directly
    const jobDateMillis = job.date || job;

    if (!jobDateMillis || isNaN(Number(jobDateMillis))) {
        return 100;
    }

    const jobDate = new Date(Number(jobDateMillis));
    const dayIndex = jobDate.getDay();

    const hebrewDays = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"];
    const jobDayInHebrew = hebrewDays[dayIndex];

    if (availableDays.includes(jobDayInHebrew)) {
        return 100; // Perfect match
    } else {
        return 0; // No match - Hard Filter will block it
    }
};

module.exports = { calculateScheduleMatch };