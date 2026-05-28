/**
 * Convert HH:MM string to total minutes from midnight.
 * Example: "08:30" -> 510 minutes.
 */
const timeToMinutes = (timeStr) => {
    const [hours, minutes] = timeStr.split(':').map(Number);
    return hours * 60 + minutes;
};

/**
 * Calculates match based on candidate's BUSY slots.
 * Returns 100 if candidate is completely free during job hours.
 */
const calculateScheduleMatch = (jobAvailability, candidateAvailability) => {
    // If candidate skipped or is always available, return perfect match
    if (candidateAvailability.is_always_available) {
        return 100;
    }

    let totalRequiredMinutes = 0;
    let totalOverlapWithBusyMinutes = 0;

    const days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];

    days.forEach(day => {
        const jobBlocks = jobAvailability[day] || [];
        // In the new layout, candidate blocks represent busy times
        const busyBlocks = candidateAvailability.busy_slots || [];
        
        // Filter busy slots for the specific day
        const dayBusyBlocks = busyBlocks.filter(slot => slot.day.toLowerCase() === day);

        jobBlocks.forEach(jBlock => {
            const jStart = timeToMinutes(jBlock.start);
            const jEnd = timeToMinutes(jBlock.end);
            totalRequiredMinutes += (jEnd - jStart);

            let blockOverlap = 0;

            dayBusyBlocks.forEach(bBlock => {
                const bStart = timeToMinutes(bBlock.start);
                const bEnd = timeToMinutes(bBlock.end);

                // Find intersection with busy hours
                const maxStart = Math.max(jStart, bStart);
                const minEnd = Math.min(jEnd, bEnd);
                
                if (maxStart < minEnd) {
                    blockOverlap += (minEnd - maxStart);
                }
            });

            totalOverlapWithBusyMinutes += blockOverlap;
        });
    });

    if (totalRequiredMinutes === 0) {
        return 100; 
    }

    // Match decreases the more the candidate is busy during job hours
    let freeMinutes = totalRequiredMinutes - totalOverlapWithBusyMinutes;
    if (freeMinutes < 0) freeMinutes = 0;

    let matchPercentage = (freeMinutes / totalRequiredMinutes) * 100;

    // Apply flexibility bonus if applicable
    if (matchPercentage < 100 && (jobAvailability.is_flexible || candidateAvailability.is_flexible)) {
        matchPercentage += 20; 
        if (matchPercentage > 100) matchPercentage = 100; 
    }

    return Math.round(matchPercentage);
};

module.exports = { calculateScheduleMatch };