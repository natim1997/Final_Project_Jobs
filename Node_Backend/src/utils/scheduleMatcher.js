/**
 * Utility function to convert HH:MM string to total minutes from midnight.
 * Example: "10:15" -> 10 * 60 + 15 = 615.
 */
const timeToMinutes = (timeStr) => {
    const [hours, minutes] = timeStr.split(':').map(Number);
    return hours * 60 + minutes;
};

/**
 * Calculates the percentage of overlap between job requirements and candidate availability.
 * Returns a score between 0 and 100.
 */
const calculateScheduleMatch = (jobAvailability, candidateAvailability) => {
    let totalRequiredMinutes = 0;
    let totalOverlapMinutes = 0;

    const days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];

    // Iterate over each day of the week
    days.forEach(day => {
        const jobBlocks = jobAvailability[day] || [];
        const candidateBlocks = candidateAvailability[day] || [];

        // Check each required time block from the job
        jobBlocks.forEach(jBlock => {
            const jStart = timeToMinutes(jBlock.start);
            const jEnd = timeToMinutes(jBlock.end);
            totalRequiredMinutes += (jEnd - jStart);

            let blockOverlap = 0;

            // Compare against all candidate time blocks for the same day
            candidateBlocks.forEach(cBlock => {
                const cStart = timeToMinutes(cBlock.start);
                const cEnd = timeToMinutes(cBlock.end);

                // Find intersection mathematically
                const maxStart = Math.max(jStart, cStart);
                const minEnd = Math.min(jEnd, cEnd);
                
                // If minEnd > maxStart, it means there is an overlap
                if (maxStart < minEnd) {
                    blockOverlap += (minEnd - maxStart);
                }
            });

            totalOverlapMinutes += blockOverlap;
        });
    });

    // If the job has no specific hours (100% flexible timing)
    if (totalRequiredMinutes === 0) {
        return 100; 
    }

    // Calculate the base match percentage
    let matchPercentage = (totalOverlapMinutes / totalRequiredMinutes) * 100;

    // Apply a bonus if either the job or candidate is marked as flexible
    if (matchPercentage < 100 && (jobAvailability.is_flexible || candidateAvailability.is_flexible)) {
        matchPercentage += 20; // 20% flexibility bonus
        if (matchPercentage > 100) matchPercentage = 100; // Cap at 100%
    }

    return Math.round(matchPercentage);
};

module.exports = { calculateScheduleMatch };