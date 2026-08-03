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

// ==========================================
// Shared city-based distance estimator
// ==========================================
// Single source of truth for "how far apart are this candidate and this job",
// used both by the location gate below AND by matchController.js/
// jobController.js to build the `distance_to_job` value sent to the Python AI
// engine. Previously those two call sites used a completely different (and
// far cruder) estimate - an exact string comparison of the raw address
// fields that almost never matched even for two locations in the same city -
// which caused the AI's own radius pre-filter to reject almost everything
// before it even got a chance to score.
//
// Returns a number (km) when it can be determined, or null when the cities
// are unknown/unmatched (caller decides how to treat "unknown").
const estimateDistanceKm = (job, candidate) => {
    const candData = candidate.candidate ? candidate.candidate : candidate;

    const candidateCity = (candData.city || extractCityFromAddress(candData.address) || "").trim();
    const jobCity = (job.city || job.location || extractCityFromAddress(job.address) || "").trim();

    if (!candidateCity || !jobCity) {
        return { distanceKm: null, candidateCity, jobCity, reason: "MISSING_CITY" };
    }

    const candCoords = cityCoordinates[candidateCity];
    const jobCoords = cityCoordinates[jobCity];

    if (candCoords && jobCoords) {
        const distanceKm = getDistanceFromLatLonInKm(candCoords.lat, candCoords.lng, jobCoords.lat, jobCoords.lng);
        return { distanceKm, candidateCity, jobCity, reason: "COORDINATES" };
    }

    if (candidateCity === jobCity) {
        return { distanceKm: 0, candidateCity, jobCity, reason: "EXACT_TEXT_MATCH" };
    }

    return { distanceKm: null, candidateCity, jobCity, reason: "NO_COORDINATES_NO_MATCH" };
};

const calculateFinalMatchScore = (job, candidate, rawAiScore) => {

    // 1. Unwrap the candidate object if it's nested (Postman JSON structure fix)
    const candData = candidate.candidate ? candidate.candidate : candidate;

    // Ensure AI score is a valid number
    let baseScore = parseFloat(rawAiScore);
    if (isNaN(baseScore)) {
        baseScore = 0;
    }

    // Default user radius to 20 if not specified
    const userRadius = candData.searchRadius || 20;

    let finalScore = baseScore;
    let status = "NO MATCH";

    // ==========================================
    // STRICT LOCATION GATEKEEPER
    // ==========================================

    const { distanceKm, candidateCity, jobCity } = estimateDistanceKm(job, candidate);

    if (distanceKm === null) {
        return {
            finalScore: 0,
            status: "NO MATCH",
            breakdown: {
                aiBaseScore: Math.round(baseScore),
                locationPenalty: "BLOCKED",
                info: !candidateCity || !jobCity
                    ? `Blocked: Missing city info (Candidate: '${candidateCity}', Job: '${jobCity}')`
                    : `Blocked: Cities do not match (${candidateCity} vs ${jobCity}) and no map data found.`
            }
        };
    }

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

    const locationReason = `Distance: ${Math.round(distanceKm)}km (Within ${userRadius}km radius)`;

    // ==========================================
    // FINAL SCORING
    // ==========================================

    // Thresholds aligned with the AI engine's rescaled display score
    // (final_pipeline.py, _rescale_display_score): 0 = disqualified,
    // 1-59 = poor match, 60+ = good potential and above. The AI engine's
    // internal raw score is stretched onto the full 0-100 range before it
    // reaches this function, calibrated so the median real relevant match
    // lands right around 60 - keep this threshold in sync with
    // _RESCALE_ANCHORS in final_pipeline.py if that calibration changes.
    if (finalScore >= 60) {
        status = "MATCH";
    } else if (finalScore >= 1) {
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

module.exports = { calculateFinalMatchScore, estimateDistanceKm };