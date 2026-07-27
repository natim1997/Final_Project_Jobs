// ==========================================
// Match Calculator Utility
// ==========================================

//  Import the external coordinates dictionary
const cityCoordinates = require('./israelCities.js');

// Helper function to extract city name from a full address string
const extractCityFromAddress = (addressString) => {
    if (!addressString) return "";
    
    // Loop through all the cities in our dictionary
    for (const city of Object.keys(cityCoordinates)) {
        // Check if the city name is inside the address string
        if (addressString.includes(city)) {
            return city;
        }
    }
    return ""; // Return empty string if no city is found
};

// Calculate distance between two coordinates in kilometers
const getDistanceFromLatLonInKm = (lat1, lon1, lat2, lon2) => {
    const R = 6371; // Radius of the earth in km
    const dLat = (lat2 - lat1) * (Math.PI / 180);
    const dLon = (lon2 - lon1) * (Math.PI / 180);
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) * 
        Math.sin(dLon/2) * Math.sin(dLon/2); 
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)); 
    return R * c; // Distance in km
};

const calculateFinalMatchScore = (job, candidate, rawAiScore) => {
    
    // Ensure AI score is a valid number
    let baseScore = parseFloat(rawAiScore);
    if (isNaN(baseScore)) {
        baseScore = 0;
    }

    // Get city strings. If city field is missing, try to extract it from the address
    const candidateCity = (candidate.city || extractCityFromAddress(candidate.address) || "").trim();
    const jobCity = (job.city || job.location || extractCityFromAddress(job.address) || "").trim();
    
    // Default user radius to 20 if not specified
    const userRadius = candidate.searchRadius || 20; 
    let finalScore = baseScore;
    let locationReason = "Location match";
    let status = "NO MATCH";

    //Check if we found coordinates for both cities
    if (cityCoordinates[candidateCity] && cityCoordinates[jobCity]) {
        const candCoords = cityCoordinates[candidateCity];
        const jobCoords = cityCoordinates[jobCity];
        
        const distanceKm = getDistanceFromLatLonInKm(candCoords.lat, candCoords.lng, jobCoords.lat, jobCoords.lng);
        
        // Strict block if distance exceeds search radius
        if (distanceKm > userRadius) {
            return {
                finalScore: 0,
                status: "NO MATCH",
                breakdown: {
                    aiBaseScore: Math.round(baseScore),
                    locationPenalty: "BLOCKED",
                    info: `Blocked: Job is ${Math.round(distanceKm)}km away (exceeds ${userRadius}km radius)`
                }
            };
        } else {
            locationReason = `Distance: ${Math.round(distanceKm)}km (Within ${userRadius}km radius)`;
        }
    } 
    else if (candidateCity && jobCity && candidateCity !== jobCity) {
        // Fallback if city is missing from the external dictionary
        finalScore = Math.max(0, baseScore - 10); 
        locationReason = `Cities do not match (Fallback penalty): ${candidateCity} vs ${jobCity}`;
    }
    else if (!jobCity) {
        // If we still don't know the job location, apply a small penalty
        finalScore = Math.max(0, baseScore - 5);
        locationReason = `Job location unknown or not in dictionary`;
    }

    // Determine final status based on score
    if (finalScore >= 75) {
        status = "MATCH";
    } else if (finalScore >= 40) {
        status = "POTENTIAL";
    }

    return {
        finalScore: Math.round(finalScore),
        status: status,
        breakdown: {
            "aiBaseScore": Math.round(baseScore),
            "locationPenalty": baseScore - finalScore,
            "info": locationReason
        }
    };
};

module.exports = { calculateFinalMatchScore };