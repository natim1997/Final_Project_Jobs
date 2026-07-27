/**
 * Schedule Matcher - Updated Version
 * 
 * Checks if the job's date matches the candidate's available days.
 * Returns 100 if it's a match (or if candidate is always available).
 * Returns 0 if the candidate is not available on the job's day.
 */
const calculateScheduleMatch = (job, candidate) => {
    // 1. Get candidate's available days
    // Support both full candidate object or just the array if passed directly
    const availableDays = candidate.availableDays || candidate || [];
    
    // If it's not an array or if it's empty, candidate is available every day
    if (!Array.isArray(availableDays) || availableDays.length === 0) {
        return 100;
    }

    // 2. Get the job's date (timestamp in milliseconds)
    // Support both full job object or just the date field if passed directly
    const jobDateMillis = job.date || job;

    // If the job does not have a date, allow it to pass
    if (!jobDateMillis || isNaN(Number(jobDateMillis))) {
        return 100; 
    }

    // 3. Convert timestamp to a JavaScript Date object
    const jobDate = new Date(Number(jobDateMillis));

    // 4. Get the day index (0 = Sunday, 1 = Monday, etc.)
    const dayIndex = jobDate.getDay();

    // 5. Convert the index to a Hebrew string
    const hebrewDays = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"];
    const jobDayInHebrew = hebrewDays[dayIndex];

    // 6. Check if the job's day is in the candidate's available days
    if (availableDays.includes(jobDayInHebrew)) {
        return 100; // Perfect match
    } else {
        return 0; // No match - Hard Filter will block it
    }
};

module.exports = { calculateScheduleMatch };