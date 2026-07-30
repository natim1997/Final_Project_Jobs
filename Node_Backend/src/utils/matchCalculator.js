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
    
    // 1. Unwrap the candidate object if it's nested (Postman JSON structure fix)
    const candData = candidate.candidate ? candidate.candidate : candidate;
    
    // Ensure AI score is a valid number
    let baseScore = parseFloat(rawAiScore);
    if (isNaN(baseScore)) {
        baseScore = 0;
    }

    // 2. Read from the unwrapped object (candData)
    const candidateCity = (candData.city || extractCityFromAddress(candData.address) || "").trim();
    const jobCity = (job.city || job.location || extractCityFromAddress(job.address) || "").trim();
    
    // Default user radius to 20 if not specified
    const userRadius = candData.searchRadius || 20; 
    
    let finalScore = baseScore;
    let locationReason = "Location match";
    let status = "NO MATCH";

    // ==========================================
    // STRICT LOCATION GATEKEEPERS
    // ==========================================

    // GATE 1: Missing city info entirely
    if (!candidateCity || !jobCity) {
        return {
            finalScore: 0,
            status: "NO MATCH",
            breakdown: {
                aiBaseScore: Math.round(baseScore),
                locationPenalty: "BLOCKED",
                info: `Blocked: Missing city info (Candidate: '${candidateCity}', Job: '${jobCity}')`
            }
        };
    }

    const candCoords = cityCoordinates[candidateCity];
    const jobCoords = cityCoordinates[jobCity];

    // GATE 2: Exact coordinate math
    if (candCoords && jobCoords) {
        const distanceKm = getDistanceFromLatLonInKm(candCoords.lat, candCoords.lng, jobCoords.lat, jobCoords.lng);
        
        if (distanceKm > userRadius) {
            return {
                finalScore: 0,
                status: "NO MATCH",
                breakdown: {
                    aiBaseScore: Math.round(baseScore),
                    locationPenalty: "BLOCKED",
                    info: `Blocked: Job is ${Math.round(distanceKm)}km away (exceeds ${userRadius}km limit)`
                }
            };
        }
        locationReason = `Distance: ${Math.round(distanceKm)}km (Within ${userRadius}km radius)`;
    } 
    // GATE 3: No coordinates found for one/both, and the text names do not match exactly
    else if (candidateCity !== jobCity) {
        return {
            finalScore: 0,
            status: "NO MATCH",
            breakdown: {
                aiBaseScore: Math.round(baseScore),
                locationPenalty: "BLOCKED",
                info: `Blocked: Cities do not match (${candidateCity} vs ${jobCity}) and no map data found.`
            }
        };
    }
    // If it reaches here without coordinates, it means candidateCity === jobCity exactly.
    else {
        locationReason = `Exact text match (${candidateCity}), assuming 0km distance.`;
    }

    // ==========================================
    // FINAL SCORING
    // ==========================================

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
            "locationPenalty": 0,
            "info": locationReason
        }
    };
};

module.exports = { calculateFinalMatchScore };